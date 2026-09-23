"""Generic contour-based detection of rectangular UI slots."""

import cv2
import numpy as np


def _overlap_ratio(first, second):
    """Intersection area divided by the smaller box area."""
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    left, top = max(ax, bx), max(ay, by)
    right, bottom = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    intersection = max(0, right - left) * max(0, bottom - top)
    return intersection / float(min(aw * ah, bw * bh))


def _deduplicate(candidates, overlap_threshold=0.75):
    """Remove nested/duplicate contours, retaining stronger rectangles."""
    candidates.sort(key=lambda item: (item[1], item[0][2] * item[0][3]), reverse=True)
    selected = []
    for box, score in candidates:
        if any(_overlap_ratio(box, kept) >= overlap_threshold for kept, _ in selected):
            continue
        selected.append((box, score))
    return selected


def find_slots(
    image_bgr,
    slot_width_range,
    slot_height_range,
    roi=None,
    aspect_ratio_range=None,
    minimum_rectangularity=0.30,
    canny_thresholds=(40, 120),
    close_kernel=(3, 3),
    maximum_slots=None,
):
    """Find independent rectangular slots using contours.

    This follows ``helpers.find_reward_slots``: preprocess the image, find
    contours, filter bounding rectangles by geometry, and remove duplicates.
    Slots do not need to form a grid or repeat at fixed intervals.

    ``roi`` is an optional ``(x, y, width, height)`` search area. Returned boxes
    use source-image coordinates and are ordered top-to-bottom, left-to-right.
    """
    if image_bgr is None or image_bgr.size == 0:
        raise ValueError("image_bgr is empty/None")

    width_min, width_max = slot_width_range
    height_min, height_max = slot_height_range
    if width_min <= 0 or width_max < width_min:
        raise ValueError("slot_width_range must be a valid positive range")
    if height_min <= 0 or height_max < height_min:
        raise ValueError("slot_height_range must be a valid positive range")
    if not 0 <= minimum_rectangularity <= 1:
        raise ValueError("minimum_rectangularity must be between 0 and 1")
    if maximum_slots is not None and maximum_slots < 1:
        raise ValueError("maximum_slots must be positive or None")

    image_height, image_width = image_bgr.shape[:2]
    offset_x, offset_y = 0, 0
    search_image = image_bgr
    if roi is not None:
        x, y, width, height = (int(value) for value in roi)
        x0, y0 = max(0, min(x, image_width)), max(0, min(y, image_height))
        x1 = max(x0, min(x + width, image_width))
        y1 = max(y0, min(y + height, image_height))
        if x0 == x1 or y0 == y1:
            return []
        offset_x, offset_y = x0, y0
        search_image = image_bgr[y0:y1, x0:x1]

    gray = cv2.cvtColor(search_image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(gray, *canny_thresholds)
    if close_kernel is not None:
        kernel_width, kernel_height = close_kernel
        if kernel_width < 1 or kernel_height < 1:
            raise ValueError("close_kernel dimensions must be positive")
        kernel = np.ones((kernel_height, kernel_width), dtype=np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if not width_min <= width <= width_max:
            continue
        if not height_min <= height <= height_max:
            continue

        aspect_ratio = width / float(height)
        if (aspect_ratio_range is not None and
                not aspect_ratio_range[0] <= aspect_ratio <= aspect_ratio_range[1]):
            continue

        box_area = width * height
        rectangularity = cv2.contourArea(contour) / float(box_area)
        if rectangularity < minimum_rectangularity:
            continue

        candidates.append(((offset_x + x, offset_y + y, width, height), rectangularity))

    selected = _deduplicate(candidates)
    if maximum_slots is not None:
        selected = sorted(selected, key=lambda item: item[1], reverse=True)[:maximum_slots]

    boxes = [box for box, _ in selected]
    boxes.sort(key=lambda box: (box[1] + box[3] * 0.5, box[0]))
    return boxes


def find_baitan_slots(image_bgr):
    """Find the visible 摆摊 listing slots in a full game screenshot."""
    if image_bgr is None or image_bgr.size == 0:
        raise ValueError("image_bgr is empty/None")

    height, width = image_bgr.shape[:2]
    return find_slots(
        image_bgr,
        slot_width_range=(int(width * 0.22), int(width * 0.28)),
        slot_height_range=(int(height * 0.10), int(height * 0.14)),
        roi=(int(width * 0.07), int(height * 0.28),
             int(width * 0.53), int(height * 0.54)),
        aspect_ratio_range=(2.4, 3.2),
        maximum_slots=8,
    )
