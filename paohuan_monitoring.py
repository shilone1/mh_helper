"""Monitor game windows for paohuan item templates and close the market.

The configured game windows are scanned roughly every 1.3 seconds.  A match
must still be present in the same window after 0.5 seconds before the market
close button is clicked and an audible alert is played.
"""

import os
import time
import winsound

import cv2
import numpy as np
import pyautogui

from app_paths import resource_path
from config import window_capture_areas_
from mouse_action import random_click_mouse


SCAN_INTERVAL_SECONDS = 1.3
CONFIRM_DELAY_SECONDS = 0.5
ITEM_MATCH_THRESHOLD = 0.90
NEIDAN_MATCH_THRESHOLD = 0.90
CLOSE_MATCH_THRESHOLD = 0.80
ACTION_MATCH_THRESHOLD = 0.80
ACTION_TIMEOUT_SECONDS = 5.0
ACTION_POLL_SECONDS = 0.20
AFTER_CLICK_DELAY_SECONDS = 0.40
MIN_ITEM_OCCURRENCES = 4
CENTER_CLICK_SQUARE_SIZE = 260

ITEM_TEMPLATE_DIR = resource_path("img_templates", "items", "paohuan_items")
NEIDAN_SOURCE_FILENAME = "neidan.png"
NEIDAN_MASK_PATH = resource_path(
    "img_templates", "items", "paohuan_items", "neidan_mask.png"
)
MARKET_CLOSE_TEMPLATE = resource_path("img_templates", "market_close.png")
BAITAN_PANEL_TEMPLATE = resource_path("img_templates", "baitan_panel_icon.png")
POST_CLOSE_TEMPLATE_PATHS = (
    ("expand icon", resource_path("img_templates", "expand_bottom.png"), False),
    ("zhuzhan panel", resource_path("img_templates", "zhuzhan_panel.png"), False),
    ("last zhuzhan selection", resource_path("img_templates", "zhuzhan_select.png"), True),
    ("close zhuzhan panel", resource_path("img_templates", "recruit_hall_close.png"), False),
    ("double-exp panel", resource_path("img_templates", "double_exp_tab.png"), False),
    ("paohuan guaji", resource_path("img_templates", "paohuan_guaji.png"), False),
)


def load_image(path):
    """Load an image while supporting non-ASCII Windows paths."""
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return image


def load_mask(path, expected_shape):
    mask = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise FileNotFoundError(f"Cannot read mask: {path}")
    if mask.shape != expected_shape[:2]:
        raise ValueError(
            f"Mask shape {mask.shape} does not match template shape "
            f"{expected_shape[:2]}: {path}"
        )
    return mask


def load_item_templates(folder):
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Paohuan template folder not found: {folder}")

    loaded = []
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith(("_mask.png", "_consensus.png")):
            continue
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
            loaded.append((filename, load_image(os.path.join(folder, filename))))

    if not loaded:
        raise RuntimeError(f"No image templates found in: {folder}")
    return [
        (
            name,
            image,
            load_mask(NEIDAN_MASK_PATH, image.shape)
            if name.lower() == NEIDAN_SOURCE_FILENAME
            else None,
        )
        for name, image in loaded
    ]


def capture_screen():
    screenshot = pyautogui.screenshot()
    return cv2.cvtColor(np.asarray(screenshot), cv2.COLOR_RGB2BGR)


def capture_window(window):
    screenshot = pyautogui.screenshot(region=window)
    return cv2.cvtColor(np.asarray(screenshot), cv2.COLOR_RGB2BGR)


def best_match(image, template, threshold, mask=None):
    """Return (local bounding box, confidence), or (None, confidence)."""
    image_height, image_width = image.shape[:2]
    template_height, template_width = template.shape[:2]
    if template_height > image_height or template_width > image_width:
        return None, 0.0

    result = cv2.matchTemplate(
        image, template, cv2.TM_CCOEFF_NORMED, mask=mask
    )
    result = np.nan_to_num(result, nan=-1.0, posinf=-1.0, neginf=-1.0)
    _, confidence, _, location = cv2.minMaxLoc(result)
    if confidence < threshold:
        return None, confidence

    x, y = location
    return (x, y, x + template_width, y + template_height), confidence


def all_matches(image, template, threshold, mask=None):
    """Return one local box per matching icon, ordered top-to-bottom."""
    image_height, image_width = image.shape[:2]
    template_height, template_width = template.shape[:2]
    if template_height > image_height or template_width > image_width:
        return []

    scores = cv2.matchTemplate(
        image, template, cv2.TM_CCOEFF_NORMED, mask=mask
    )
    scores = np.nan_to_num(scores, nan=-1.0, posinf=-1.0, neginf=-1.0)
    # Keep only local score peaks so one icon does not produce many overlapping
    # boxes. Sorting by screen position makes "last" mean the bottom-most icon.
    peak_kernel = np.ones((template_height, template_width), dtype=np.uint8)
    local_maxima = scores == cv2.dilate(scores, peak_kernel)
    ys, xs = np.where((scores >= threshold) & local_maxima)
    matches = [
        (
            (int(x), int(y), int(x + template_width), int(y + template_height)),
            float(scores[y, x]),
        )
        for y, x in zip(ys, xs)
    ]
    return sorted(matches, key=lambda match: (match[0][1], match[0][0]))


def find_item(image, templates):
    """Return the strongest item match in an image."""
    strongest = None
    for filename, template, mask in templates:
        threshold = NEIDAN_MATCH_THRESHOLD if mask is not None else ITEM_MATCH_THRESHOLD
        box, confidence = best_match(image, template, threshold, mask=mask)
        if box and (strongest is None or confidence > strongest[2]):
            strongest = filename, box, confidence, template, mask
    return strongest


def crop_window(full_screen, window):
    left, top, width, height = window
    return full_screen[top : top + height, left : left + width]


def click_local_box(window, box):
    global_box = local_to_global_box(window, box)
    x1, y1, x2, y2 = global_box
    pyautogui.click((x1 + x2) // 2, (y1 + y2) // 2)


def local_to_global_box(window, box):
    left, top, _, _ = window
    x1, y1, x2, y2 = box
    return left + x1, top + y1, left + x2, top + y2


def random_click_window_center(window):
    left, top, width, height = window
    size = min(CENTER_CLICK_SQUARE_SIZE, width, height)
    x1 = left + (width - size) // 2
    y1 = top + (height - size) // 2
    area = (x1, y1, x1 + size, y1 + size)
    clicked_at = random_click_mouse(area, center_bias=False)
    print(f"  Random center-area click at {clicked_at}.")


def sound_alert():
    """Play a noticeable two-tone Windows alert."""
    winsound.Beep(1100, 250)
    winsound.Beep(1500, 400)


def sound_success():
    """Play a distinct ascending sound when a window is unflagged."""
    winsound.Beep(900, 150)
    winsound.Beep(1300, 150)
    winsound.Beep(1800, 300)


def wait_and_click(window, label, template, choose_last=False):
    """Wait for a template in one window and click it."""
    deadline = time.monotonic() + ACTION_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        window_image = capture_window(window)
        if choose_last:
            matches = all_matches(window_image, template, ACTION_MATCH_THRESHOLD)
            if matches:
                box, confidence = matches[-1]
            else:
                box, confidence = None, None
        else:
            box, confidence = best_match(
                window_image, template, ACTION_MATCH_THRESHOLD
            )

        if box is not None:
            random_click_mouse(local_to_global_box(window, box))
            print(f"  Clicked {label} ({confidence:.3f}).")
            time.sleep(AFTER_CLICK_DELAY_SECONDS)
            return True
        time.sleep(ACTION_POLL_SECONDS)

    print(f"  Timed out waiting for {label}; post-close sequence stopped.")
    return False


def run_post_close_sequence(window, action_templates):
    """Run the requested navigation sequence inside the triggering window."""
    random_click_window_center(window)
    for label, template, choose_last in action_templates:
        clicked = wait_and_click(
            window, label, template, choose_last=choose_last
        )
        if not clicked:
            return False
    return True


def monitor():
    item_templates = load_item_templates(ITEM_TEMPLATE_DIR)
    market_close = load_image(MARKET_CLOSE_TEMPLATE)
    baitan_panel = load_image(BAITAN_PANEL_TEMPLATE)
    action_templates = [
        (label, load_image(path), choose_last)
        for label, path, choose_last in POST_CLOSE_TEMPLATE_PATHS
    ]
    flagged_windows = set()

    print(f"Loaded {len(item_templates)} paohuan item templates.")
    print("Monitoring started. Press Ctrl+C to stop.")

    while True:
        scan_started = time.monotonic()
        full_screen = capture_screen()

        for window_number, window in enumerate(window_capture_areas_, start=1):
            window_image = crop_window(full_screen, window)

            if window_number in flagged_windows:
                close_box, close_confidence = best_match(
                    window_image, market_close, CLOSE_MATCH_THRESHOLD
                )
                if close_box is not None:
                    click_local_box(window, close_box)
                    flagged_windows.remove(window_number)
                    print(
                        f"Window {window_number}: market close returned "
                        f"({close_confidence:.3f}); clicked it and cleared flag."
                    )
                    sound_success()
                continue

            first_match = find_item(window_image, item_templates)
            if first_match is None:
                continue

            filename, _, first_confidence, matched_template, matched_mask = first_match
            print(
                f"Window {window_number}: possible {filename} "
                f"({first_confidence:.3f}); confirming..."
            )

            time.sleep(CONFIRM_DELAY_SECONDS)
            confirmed_window = capture_window(window)
            item_threshold = (
                NEIDAN_MATCH_THRESHOLD
                if matched_mask is not None
                else ITEM_MATCH_THRESHOLD
            )
            confirmed_matches = all_matches(
                confirmed_window,
                matched_template,
                item_threshold,
                mask=matched_mask,
            )
            if not confirmed_matches:
                print(f"Window {window_number}: match disappeared; ignored.")
                continue
            confirmed_confidence = max(score for _, score in confirmed_matches)

            baitan_box, baitan_confidence = best_match(
                confirmed_window, baitan_panel, ACTION_MATCH_THRESHOLD
            )
            if baitan_box is None:
                print(
                    f"Window {window_number}: {filename} confirmed, but "
                    "baitan_panel_icon.png was not found; ignored."
                )
                continue

            if len(confirmed_matches) < MIN_ITEM_OCCURRENCES:
                print(
                    f"Window {window_number}: {filename} confirmed in baitan, "
                    f"but found only {len(confirmed_matches)}/"
                    f"{MIN_ITEM_OCCURRENCES} copies; ignored."
                )
                continue

            print(
                f"Window {window_number}: confirmed {len(confirmed_matches)} "
                f"copies of {filename}; baitan panel confidence "
                f"{baitan_confidence:.3f}."
            )

            close_box, close_confidence = best_match(
                confirmed_window, market_close, CLOSE_MATCH_THRESHOLD
            )
            if close_box is None:
                print(
                    f"Window {window_number}: {filename} confirmed "
                    f"({confirmed_confidence:.3f}), but market_close.png was not found."
                )
                continue

            click_local_box(window, close_box)
            print(
                f"Window {window_number}: confirmed {filename} "
                f"({confirmed_confidence:.3f}); clicked market close "
                f"({close_confidence:.3f})."
            )
            sound_alert()
            if run_post_close_sequence(window, action_templates):
                flagged_windows.add(window_number)
                print(
                    f"Window {window_number}: post-close sequence completed; "
                    "window flagged until market close appears again."
                )

        remaining = SCAN_INTERVAL_SECONDS - (time.monotonic() - scan_started)
        if remaining > 0:
            time.sleep(remaining)


if __name__ == "__main__":
    try:
        monitor()
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
