"""Read 摆摊 comparison listings and recommend a matching sale price."""

import re
from functools import lru_cache

import cv2

from app_paths import resource_path
from slot_detection import find_slots


REFERENCE_WIDTH = 631
REFERENCE_HEIGHT = 479


def _scaled_rect(image_bgr, rect, translation=(0, 0)):
    """Scale and translate a reference-image rectangle."""
    _, width = image_bgr.shape[:2]
    # Game captures can include extra title-bar height without resizing their
    # content, so derive a uniform content scale from width.
    scale_x = width / REFERENCE_WIDTH
    scale_y = scale_x
    translate_x, translate_y = translation
    x0, y0, x1, y1 = rect
    return (
        int(round(x0 * scale_x + translate_x)),
        int(round(y0 * scale_y + translate_y)),
        int(round(x1 * scale_x + translate_x)),
        int(round(y1 * scale_y + translate_y)),
    )


def _crop(image_bgr, rect):
    x0, y0, x1, y1 = rect
    return image_bgr[y0:y1, x0:x1]


def _read_text(ocr, image_bgr, rect, scale=4, contrast=False):
    """OCR a tight field and return its joined text and weakest confidence."""
    if rect is None:
        return "", 0.0
    field = _crop(image_bgr, rect)
    if field.size == 0:
        return "", 0.0
    field = cv2.resize(field, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    if contrast:
        gray = cv2.cvtColor(field, cv2.COLOR_BGR2GRAY)
        field = cv2.cvtColor(cv2.createCLAHE(2.0, (4, 4)).apply(gray), cv2.COLOR_GRAY2BGR)
    result = ocr.ocr(field, cls=False)
    entries = result[0] if result and result[0] else []
    if not entries:
        return "", 0.0
    return "".join(entry[1][0] for entry in entries), min(entry[1][1] for entry in entries)


def _number(text):
    digits = re.findall(r"\d+", text or "")
    return int("".join(digits)) if digits else None


@lru_cache(maxsize=3)
def _price_template(name):
    path = resource_path("img_templates", name + ".png")
    template = cv2.imread(path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Cannot read price template: {path}")
    return template


def _find_price_icon(image_bgr, name, region, threshold=0.85):
    """Match inside a bounded region and return image-local corner coordinates."""
    height, width = image_bgr.shape[:2]
    x0, y0, x1, y1 = region
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(width, x1), min(height, y1)
    template = _price_template(name)
    th, tw = template.shape[:2]
    if x1 - x0 < tw or y1 - y0 < th:
        return None
    result = cv2.matchTemplate(image_bgr[y0:y1, x0:x1], template, cv2.TM_CCOEFF_NORMED)
    _, score, _, location = cv2.minMaxLoc(result)
    if score < threshold:
        return None
    x, y = x0 + location[0], y0 + location[1]
    return (x, y, x + tw, y + th)


def _coin_price_area(image_bgr, region, right_edge):
    coin = _find_price_icon(image_bgr, "gold_icon", region)
    if coin is None or right_edge <= coin[2] + 1:
        return None
    # Exclude the coin itself and keep only the number's horizontal band.
    return (coin[2] + 1, coin[1], right_edge, coin[3])


def _target_price_area(image_bgr):
    height, width = image_bgr.shape[:2]
    right_half = (width // 2, 0, width, height)
    minus = _find_price_icon(image_bgr, "price_decrease", right_half)
    plus = _find_price_icon(image_bgr, "price_increase", right_half)
    if minus is None or plus is None or minus[2] >= plus[0]:
        return None
    if abs((minus[1] + minus[3]) - (plus[1] + plus[3])) > 10:
        return None
    between_buttons = (minus[2], min(minus[1], plus[1]),
                       plus[0], max(minus[3], plus[3]))
    return _coin_price_area(image_bgr, between_buttons, plus[0] - 2)


def _make_ocr():
    try:
        from paddleocr import PaddleOCR
    except ImportError as error:
        raise RuntimeError("PaddleOCR is required for pricing recognition") from error
    return PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)


def _find_listing_boxes(image_bgr):
    """Detect complete comparison rows on the left side of the dialog."""
    height, width = image_bgr.shape[:2]
    scale_x = width / REFERENCE_WIDTH
    scale_y = scale_x
    roi_x0, roi_y0, roi_x1, roi_y1 = _scaled_rect(image_bgr, (90, 105, 315, 405))
    return find_slots(
        image_bgr,
        slot_width_range=(int(145 * scale_x), int(180 * scale_x)),
        slot_height_range=(int(43 * scale_y), int(70 * scale_y)),
        roi=(roi_x0, roi_y0, roi_x1 - roi_x0, roi_y1 - roi_y0),
        aspect_ratio_range=(2.2, 4.0),
        minimum_rectangularity=0.25,
    )


def analyze_baitan_pricing(image_bgr, ocr=None, minimum_confidence=0.70,
                           ocr_scale=4, ocr_contrast=False):
    """Read the target item and use only the top complete market listing.

    The top listing is compared by numeric level when the target has one.
    Item names are retained for diagnostics only. The result is data only; this
    function does not click or change the game's price.
    """
    if image_bgr is None or image_bgr.size == 0:
        raise ValueError("image_bgr is empty/None")
    if ocr is None:
        ocr = _make_ocr()

    def read_text(ocr, image, rect):
        return _read_text(ocr, image, rect, scale=ocr_scale, contrast=ocr_contrast)

    listing_boxes = sorted(_find_listing_boxes(image_bgr), key=lambda box: box[1])
    translation = (0, 0)
    if listing_boxes:
        scale = image_bgr.shape[1] / REFERENCE_WIDTH
        translation = (
            listing_boxes[0][0] - int(round(114 * scale)),
            listing_boxes[0][1] - int(round(127 * scale)),
        )

    target_name, target_name_conf = read_text(
        ocr, image_bgr, _scaled_rect(image_bgr, (380, 75, 465, 103), translation)
    )
    target_level_text, target_level_conf = read_text(
        ocr, image_bgr, _scaled_rect(image_bgr, (380, 96, 470, 123), translation)
    )
    target_price_area = _target_price_area(image_bgr)
    target_price_text, target_price_conf = read_text(ocr, image_bgr, target_price_area)
    target_level = _number(target_level_text)
    compare_level = target_level is not None
    current_price = _number(target_price_text)

    scale_x = image_bgr.shape[1] / REFERENCE_WIDTH
    scale_y = scale_x
    listings = []
    for index, (x, y, width, height) in enumerate(listing_boxes):
        name_rect = (
            x + int(40 * scale_x), y - int(2 * scale_y),
            x + width, y + int(23 * scale_y),
        )
        level_rect = (
            x + int(8 * scale_x), y + int(20 * scale_y),
            x + int(50 * scale_x), y + height,
        )
        price_rect = _coin_price_area(
            image_bgr, (x, y, x + width, y + height), x + width - 2
        )
        name, name_conf = read_text(ocr, image_bgr, name_rect)
        level_text, level_conf = read_text(ocr, image_bgr, level_rect)
        price_text, price_conf = read_text(ocr, image_bgr, price_rect)
        level, price = _number(level_text), _number(price_text)
        reliable = (
            price_conf >= minimum_confidence
            and (not compare_level or (level_conf >= minimum_confidence and level is not None))
            and price is not None
        )
        matches = (
            reliable
            and (not compare_level or level == target_level)
        )
        listings.append({
            "index": index,
            "box": (x, y, width, height),
            "item_name": name,
            "level": level,
            "price": price,
            "price_area": price_rect,
            "confidence": min(level_conf, price_conf) if compare_level else price_conf,
            "matches_target": matches,
        })

    target_reliable = (
        (not compare_level or target_level_conf >= minimum_confidence)
        and target_price_conf >= minimum_confidence
        and current_price is not None
    )
    reference = (
        listings[0] if target_reliable and listings and listings[0]["matches_target"]
        else None
    )
    return {
        "item_name": target_name,
        "level": target_level,
        "current_price": current_price,
        "price_area": target_price_area,
        "target_confidence": (
            min(target_level_conf, target_price_conf)
            if compare_level else target_price_conf
        ),
        "target_reliable": target_reliable,
        "target_level_confidence": target_level_conf,
        "target_price_confidence": target_price_conf,
        "target_level_text": target_level_text,
        "target_price_text": target_price_text,
        "listings": listings,
        "reference_price": reference["price"] if reference else None,
        "matched_listing_index": reference["index"] if reference else None,
    }
