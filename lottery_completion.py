"""Visual completion checks for the gray lottery coating (BGR images)."""

import time

import cv2
import numpy as np


def coating_is_cleared(image):
    """Require exposed gold in all three reward sections and almost no gray.

    Ignore the permanent outer border. Thresholds allow isolated antialiasing
    pixels, but reject remaining connected coating patches. This detects the
    revealed background, not the identity or count of the reward items.
    """
    if image is None or image.ndim != 3 or min(image.shape[:2]) < 12:
        return False
    hsv = cv2.cvtColor(image[4:-4, 4:-4], cv2.COLOR_BGR2HSV)
    gray = cv2.inRange(hsv, (0, 0, 105), (179, 35, 210))
    gold = cv2.inRange(hsv, (12, 65, 130), (38, 255, 255))
    if np.mean(gray > 0) > 0.02:
        return False
    for gray_section, gold_section in zip(np.array_split(gray, 3, axis=1),
                                          np.array_split(gold, 3, axis=1)):
        if np.mean(gray_section > 0) > 0.04 or np.mean(gold_section > 0) < 0.25:
            return False
    _, _, stats, _ = cv2.connectedComponentsWithStats(gray, connectivity=8)
    return not np.any(stats[1:, cv2.CC_STAT_AREA] > 12)


def make_completion_check(area, window, panel_template_path):
    """Build a check scoped to this card and a fixed visible lottery panel."""
    import pyautogui
    from image_matching import find_matches

    template = cv2.imread(panel_template_path)
    wx, wy, width, height = map(int, window)
    left, top, right, bottom = map(int, area)
    if template is None or not (wx <= left < right <= wx + width
                                and wy <= top < bottom <= wy + height):
        return lambda: False

    def capture():
        return cv2.cvtColor(np.array(pyautogui.screenshot(region=window)),
                            cv2.COLOR_RGB2BGR)

    anchor, _ = find_matches(capture(), template, threshold=0.8)
    if anchor is None:
        return lambda: False
    ax, ay, bx, by = anchor

    def cleared_frame():
        frame = capture()
        # A closed, moved or obscured panel is not successful scratching.
        panel, _ = find_matches(frame[ay:by, ax:bx], template, threshold=0.8)
        return panel is not None and coating_is_cleared(
            frame[top - wy:bottom - wy, left - wx:right - wx])

    def check():
        if not cleared_frame():
            return False
        time.sleep(0.15)
        return cleared_frame()

    return check
