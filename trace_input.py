"""Detect and input dark glyph traces shown inside a game drawing area.

Run this file directly to scan the screen and trace every detected glyph.
"""

import random
import time

import cv2
import numpy as np
import pyautogui

import image_matching as image_match
from app_paths import resource_path
from logger import logger
from mouse_action import (
    MOUSEEVENTF_ABSOLUTE,
    MOUSEEVENTF_MOVE,
    MOUSEINPUT,
    hold_left_mouse_button,
    move_mouse_smooth,
    normalize_coordinates,
    release_left_mouse_button,
    random_click_mouse,
    send_input,
)


TAYIN_COMPLETE_PATH = resource_path("img_templates", "tayin_complete.png")
TAYIN_DETECT_PATH = resource_path("img_templates", "tayin_detect.png")


def extract_dark_glyph(image_bgr, min_component_area=80):
    """Return the tan glyph while explicitly excluding the guide colors."""
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    hue, saturation, value = cv2.split(hsv)

    glyph_candidates = (
        (value < 248)
        & (saturation >= 15)
        & (hue >= 5)
        & (hue <= 45)
    )
    guide_pixels = (hue < 12) | (value > 240)
    mask = (glyph_candidates & ~guide_pixels).astype(np.uint8) * 255

    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    cleaned = np.zeros_like(mask)
    for label in range(1, count):
        _, _, _, _, area = stats[label]
        if area >= min_component_area:
            cleaned[labels == label] = 255
    return cleaned


def _thin(binary_mask):
    """Zhang-Suen skeletonization without requiring opencv-contrib."""
    image = (binary_mask > 0).astype(np.uint8)
    changed = True
    while changed:
        changed = False
        for phase in (0, 1):
            padded = np.pad(image, 1)
            p2 = padded[:-2, 1:-1]
            p3 = padded[:-2, 2:]
            p4 = padded[1:-1, 2:]
            p5 = padded[2:, 2:]
            p6 = padded[2:, 1:-1]
            p7 = padded[2:, :-2]
            p8 = padded[1:-1, :-2]
            p9 = padded[:-2, :-2]
            neighbours = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            transitions = (
                (p2 == 0) & (p3 == 1)
            ).astype(np.uint8)
            for first, second in ((p3, p4), (p4, p5), (p5, p6), (p6, p7),
                                  (p7, p8), (p8, p9), (p9, p2)):
                transitions += ((first == 0) & (second == 1)).astype(np.uint8)
            if phase == 0:
                preserve_a = p2 * p4 * p6 == 0
                preserve_b = p4 * p6 * p8 == 0
            else:
                preserve_a = p2 * p4 * p8 == 0
                preserve_b = p2 * p6 * p8 == 0
            remove = (
                (image == 1) & (neighbours >= 2) & (neighbours <= 6)
                & (transitions == 1) & preserve_a & preserve_b
            )
            if np.any(remove):
                image[remove] = 0
                changed = True
    return image


def build_trace_paths(glyph_mask, minimum_path_pixels=8):
    """Build one continuous graph walk for each skeleton component."""
    skeleton = _thin(glyph_mask)
    pixels = {tuple(point) for point in np.argwhere(skeleton)}
    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
               (0, 1), (1, -1), (1, 0), (1, 1)]
    paths = []

    while pixels:
        component = set()
        stack = [next(iter(pixels))]
        while stack:
            point = stack.pop()
            if point in component:
                continue
            component.add(point)
            y, x = point
            stack.extend((y + dy, x + dx) for dy, dx in offsets
                         if (y + dy, x + dx) in pixels and (y + dy, x + dx) not in component)
        pixels.difference_update(component)
        if len(component) < minimum_path_pixels:
            continue

        def neighbours(point):
            y, x = point
            return [(y + dy, x + dx) for dy, dx in offsets
                    if (y + dy, x + dx) in component]

        endpoints = [point for point in component if len(neighbours(point)) == 1]
        start = min(endpoints or component)
        visited_edges = set()
        walk = [start]

        # Store DFS frames explicitly: long glyphs can exceed Python's call
        # stack. Keep the same edge order and return steps as recursive DFS.
        frames = [(start, iter(neighbours(start)))]
        while frames:
            point, remaining = frames[-1]
            neighbour = next(remaining, None)
            if neighbour is None:
                frames.pop()
                if frames:
                    walk.append(frames[-1][0])
                continue
            edge = frozenset((point, neighbour))
            if edge in visited_edges:
                continue
            visited_edges.add(edge)
            walk.append(neighbour)
            frames.append((neighbour, iter(neighbours(neighbour))))
        paths.append([(x, y) for y, x in walk])

    return sorted(paths, key=len, reverse=True)


def widen_trace_path(centerline, glyph_mask, width_ratio=0.55, tangent_span=3):
    """Trace one side forward and the opposite side on the return journey."""
    if len(centerline) < 2:
        return centerline

    # The graph walk normally retraces edges while unwinding its DFS. Keep the
    # shortest prefix that has reached every centerline pixel; our second rail
    # becomes the deliberate return path instead.
    unique_total = len(set(centerline))
    seen = set()
    ordered = []
    for point in centerline:
        ordered.append(point)
        seen.add(point)
        if len(seen) == unique_total:
            break

    distance = cv2.distanceTransform(
        (glyph_mask > 0).astype(np.uint8), cv2.DIST_L2, 5
    )
    height, width = glyph_mask.shape

    def offset_point(index, side):
        x, y = ordered[index]
        before_x, before_y = ordered[max(0, index - tangent_span)]
        after_x, after_y = ordered[min(len(ordered) - 1, index + tangent_span)]
        dx = after_x - before_x
        dy = after_y - before_y
        tangent_length = (dx * dx + dy * dy) ** 0.5
        if tangent_length == 0:
            return x, y

        normal_x = -dy / tangent_length
        normal_y = dx / tangent_length
        offset = float(distance[y, x]) * width_ratio

        # Sharp corners can put a full offset outside the glyph. Gradually
        # shorten it until the generated point is safely inside the mask.
        for scale in (1.0, 0.8, 0.6, 0.4, 0.2, 0.0):
            candidate_x = int(round(x + side * normal_x * offset * scale))
            candidate_y = int(round(y + side * normal_y * offset * scale))
            if (0 <= candidate_x < width and 0 <= candidate_y < height
                    and glyph_mask[candidate_y, candidate_x] > 0):
                return candidate_x, candidate_y
        return x, y

    first_rail = [offset_point(index, 1) for index in range(len(ordered))]
    second_rail = [offset_point(index, -1) for index in range(len(ordered) - 1, -1, -1)]

    widened = []
    for point in first_rail + second_rail:
        if not widened or point != widened[-1]:
            widened.append(point)
    return widened


def widen_trace_paths(paths, glyph_mask, width_ratio=0.55):
    """Apply the two-rail widening strategy to all glyph components."""
    return [widen_trace_path(path, glyph_mask, width_ratio) for path in paths]


def _move_held(x, y):
    normalized_x, normalized_y = normalize_coordinates(x, y)
    send_input(MOUSEINPUT(
        dx=normalized_x, dy=normalized_y, mouseData=0,
        dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
        time=0, dwExtraInfo=None,
    ))


def input_trace_paths(paths, origin, point_delay=0.002):
    """Draw detected local-coordinate paths at the given screen origin."""
    origin_x, origin_y = origin
    for path in paths:
        screen_path = [(origin_x + x, origin_y + y) for x, y in path]
        start_x, start_y = screen_path[0]
        move_mouse_smooth(start_x, start_y, duration=0.12)
        hold_left_mouse_button(start_x, start_y)
        try:
            for x, y in screen_path[1:]:
                _move_held(x, y)
                time.sleep(point_delay)
        finally:
            end_x, end_y = screen_path[-1]
            release_left_mouse_button(end_x, end_y)


def trace_dark_glyph(area, point_delay=0.002, debug_path=None):
    """Capture, detect, and trace a glyph within ``(left, top, right, bottom)``."""
    left, top, right, bottom = (int(value) for value in area)
    screenshot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))
    image_bgr = cv2.cvtColor(np.asarray(screenshot), cv2.COLOR_RGB2BGR)
    glyph_mask = extract_dark_glyph(image_bgr)
    paths = widen_trace_paths(build_trace_paths(glyph_mask), glyph_mask)
    if not paths:
        logger.warning(f"No dark trace glyph detected in area {area}")
        return False
    if debug_path:
        cv2.imwrite(debug_path, glyph_mask)
    logger.info(f"Detected trace glyph in {len(paths)} connected stroke(s)")
    input_trace_paths(paths, (left, top), point_delay=point_delay)
    return True


def find_trace_areas(screen_bgr):
    """Find the red/pink square frames surrounding trace glyphs."""
    hsv = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2HSV)
    # The guide frame becomes more orange and more saturated when the image is
    # scaled by Windows Photos, so keep this range deliberately broad. The
    # four-side coverage check below provides the shape discrimination.
    red = cv2.inRange(hsv, np.array([0, 10, 150]), np.array([15, 255, 255]))
    contours, _ = cv2.findContours(red, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if not (130 <= width <= 260 and 130 <= height <= 260):
            continue
        if not 0.85 <= width / height <= 1.15:
            continue

        # A real writing square has red pixels along all four sides. This
        # rejects similarly sized red UI decorations elsewhere on the screen.
        edge_pixels = red[y:y + height, x:x + width]
        edge = max(3, min(width, height) // 30)
        side_coverage = (
            np.count_nonzero(edge_pixels[:edge]) / edge_pixels[:edge].size,
            np.count_nonzero(edge_pixels[-edge:]) / edge_pixels[-edge:].size,
            np.count_nonzero(edge_pixels[:, :edge]) / edge_pixels[:, :edge].size,
            np.count_nonzero(edge_pixels[:, -edge:]) / edge_pixels[:, -edge:].size,
        )
        if min(side_coverage) < 0.12:
            continue

        # Stay just inside the outer frame. Four pixels also avoids cutting
        # through the anti-aliased guide line at the scale used by the game.
        inset = 4
        area = (x + inset, y + inset, x + width - inset, y + height - inset)
        crop = screen_bgr[area[1]:area[3], area[0]:area[2]]
        if cv2.countNonZero(extract_dark_glyph(crop)) < 80:
            continue
        candidates.append(area)

    # RETR_LIST sees both the inner and outer borders of the same box. Keep
    # the largest candidate whenever one candidate substantially contains
    # another, preventing the same glyph from being traced twice.
    areas = []
    candidates.sort(key=lambda item: (item[2] - item[0]) * (item[3] - item[1]), reverse=True)
    for area in candidates:
        left, top, right, bottom = area
        area_size = (right - left) * (bottom - top)
        duplicate = False
        for kept in areas:
            intersection_width = max(0, min(right, kept[2]) - max(left, kept[0]))
            intersection_height = max(0, min(bottom, kept[3]) - max(top, kept[1]))
            intersection = intersection_width * intersection_height
            if intersection / min(area_size, (kept[2] - kept[0]) * (kept[3] - kept[1])) > 0.8:
                duplicate = True
                break
        if not duplicate:
            areas.append(area)
    return sorted(areas, key=lambda area: (area[1], area[0]))


def trace_glyphs_on_screen(point_delay=0.002):
    """Screenshot the full screen, find trace prompts, and complete them."""
    screenshot = pyautogui.screenshot()
    screen_bgr = cv2.cvtColor(np.asarray(screenshot), cv2.COLOR_RGB2BGR)
    areas = find_trace_areas(screen_bgr)
    if not areas:
        logger.info("No glyph trace prompt found on screen")
        return 0

    completed = 0
    for left, top, right, bottom in areas:
        crop = screen_bgr[top:bottom, left:right]
        glyph_mask = extract_dark_glyph(crop)
        paths = widen_trace_paths(build_trace_paths(glyph_mask), glyph_mask)
        if not paths:
            continue
        logger.info(f"Tracing glyph at {(left, top, right, bottom)} with {len(paths)} stroke(s)")
        input_trace_paths(paths, (left, top), point_delay=point_delay)
        completed += 1
    return completed


def detect_trace_prompt(screen_bgr, threshold=0.8):
    """Confirm the task using its fixed label, independently of the glyph."""
    template = cv2.imread(TAYIN_DETECT_PATH, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Trace detection template missing: {TAYIN_DETECT_PATH}")
    prompt, confidence = image_match.find_matches(
        screen_bgr, template, threshold=threshold
    )
    if prompt is not None:
        logger.info(f"Detected trace task label at {prompt}; score={confidence}")
    return prompt is not None


def detect_trace_areas(screen_area):
    """Check once for trace squares inside one game window.

    ``screen_area`` uses the project's ``(left, top, width, height)`` format.
    Both local crop coordinates and absolute mouse coordinates are returned.
    """
    window_left, window_top, _, _ = screen_area
    screenshot = pyautogui.screenshot(region=screen_area)
    screen_bgr = cv2.cvtColor(np.asarray(screenshot), cv2.COLOR_RGB2BGR)
    if not detect_trace_prompt(screen_bgr):
        return screen_bgr, None
    areas = []
    for local_area in find_trace_areas(screen_bgr):
        left, top, right, bottom = local_area
        absolute_area = (
            window_left + left,
            window_top + top,
            window_left + right,
            window_top + bottom,
        )
        areas.append((local_area, absolute_area))
    return screen_bgr, areas


def click_complete_button(screen_area, timeout=10.0, threshold=0.8):
    """Wait for and click the trace dialog's Complete button."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        button, confidence = image_match.find_icon_on_screen(
            TAYIN_COMPLETE_PATH, screen_area=screen_area, threshold=threshold
        )
        if button is not None:
            logger.info(f"Clicking trace Complete button at {button}; score={confidence}")
            random_click_mouse(button, quick_mode=True)
            return True
        time.sleep(0.5)
    logger.warning("Trace Complete button was not found")
    return False


def run_full_trace_procedure(screen_area, rounds=2, detection_delay=(5.0, 7.0)):
    """Complete the game's two consecutive glyph-tracing rounds."""
    for round_number in range(1, rounds + 1):
        delay = random.uniform(*detection_delay)
        logger.info(f"Round {round_number}: waiting {delay:.1f} seconds for optional trace prompt")
        time.sleep(delay)

        screen_bgr, areas = detect_trace_areas(screen_area)
        if areas is None:
            logger.info(f"Round {round_number}: optional trace prompt did not appear; skipping")
            return None
        if not areas:
            logger.warning(f"Round {round_number}: trace task detected, but drawing area could not be located")
            return False

        for local_area, absolute_area in areas:
            local_left, local_top, local_right, local_bottom = local_area
            crop = screen_bgr[local_top:local_bottom, local_left:local_right]
            glyph_mask = extract_dark_glyph(crop)
            paths = widen_trace_paths(build_trace_paths(glyph_mask), glyph_mask)
            if not paths:
                logger.warning(f"Round {round_number}: glyph pixels could not be traced")
                return False
            logger.info(
                f"Round {round_number}: tracing glyph at "
                f"{absolute_area} with {len(paths)} stroke(s)"
            )
            input_trace_paths(paths, (absolute_area[0], absolute_area[1]))

        if not click_complete_button(screen_area):
            return False

        # Give the dialog time to replace the completed glyph before scanning
        # for the second round.
        if round_number < rounds:
            time.sleep(2.0)
    return True


def main():
    raise SystemExit(
        "trace_input.py is now integrated into Shimen and requires a game window area"
    )


if __name__ == "__main__":
    raise SystemExit(main())
