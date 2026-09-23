"""Use huoli once in each configured window. Run: python huoli_utilize.py."""

import random
import time
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

import cv2
import numpy as np
import pyautogui

from app_paths import resource_path
from baitan_pricing import analyze_baitan_pricing, _make_ocr
from config import (
    inventory_path, window_capture_areas_, inventory_additional_options_path,
    market_to_sell_path, market_launch_path, confirm_seven_days_path,
    market_sell_confirm_path, market_close_path, inventory_arrange_path,
)
from image_matching import find_icon_on_screen, find_icon_each_window, find_icons_one_per_window
from mouse_action import random_click_mouse as _random_click_mouse
from mouse_action import hold_left_mouse_button, release_left_mouse_button, move_mouse_smooth
from slot_detection import find_baitan_slots
from logger import logger


TEMPLATE_PATH = resource_path("img_templates", "huoli_utilize.png")
OPEN_AREA = (585, 37, 629, 83)
USE_AREA = (470, 304, 520, 325)
TEMPLATE_ATTEMPTS = 5


def validate_click_area(area):
    """Reject invalid screen coordinates before sending mouse input."""
    x1, y1, x2, y2 = (int(value) for value in area)
    width, height = pyautogui.size()
    inside_window = any(
        left <= x1 <= x2 < left + w and top <= y1 <= y2 < top + h
        for left, top, w, h in window_capture_areas_
    )
    if not (0 <= x1 <= x2 < width and 0 <= y1 <= y2 < height and inside_window):
        raise ValueError(f"Refusing click outside game windows/screen: {area}; screen={width}x{height}")
    return (x1, y1, x2, y2)


def random_click_mouse(area):
    if area is None:
        return False
    area = validate_click_area(area)
    print(f"Click bounds: {area}", flush=True)
    return _random_click_mouse(area)


def hold_skill_button(area):
    x1, y1, x2, y2 = validate_click_area(area)
    x, y = (x1 + x2) // 2, (y1 + y2) // 2
    seconds = random.uniform(3.0, 5.0)
    print(f"Holding skill button at {(x, y)} for {seconds:.2f}s.")
    move_mouse_smooth(x, y, duration=random.uniform(0.2, 0.4))
    try:
        hold_left_mouse_button(x, y)
        time.sleep(seconds)
    finally:
        release_left_mouse_button(x, y)


def save_market_diagnostic(window, reason, pricing=None):
    folder = Path(resource_path("pricing_diagnostics"))
    folder.mkdir(exist_ok=True)
    name = f"window_{window[0]}_{window[1]}_{time.time_ns()}_{reason}"
    pyautogui.screenshot(region=window).save(str(folder / (name + ".png")))
    if pricing is not None:
        (folder / (name + ".json")).write_text(
            json.dumps(pricing, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(f"Window {window[:2]}: {reason}; saved {folder / name}", flush=True)


def offset_area(area, window):
    """Translate a local click rectangle using the window's left/top origin."""
    left, top = window[:2]
    x1, y1, x2, y2 = area
    return (left + x1, top + y1, left + x2, top + y2)


def precheck_baitan_slots():
    """Return free slots by window; omit windows whose navigation failed."""
    slots_left = {}
    for index, window in enumerate(window_capture_areas_, start=1):
        for filename in ("shangcheng.png", "baitan.png", "want_to_chushou.png"):
            for attempt in range(TEMPLATE_ATTEMPTS):
                time.sleep(random.uniform(0.5, 0.8))
                match, _ = find_icon_on_screen(
                    resource_path("img_templates", filename), screen_area=window
                )
                if match is not None:
                    random_click_mouse(match)
                    time.sleep(random.uniform(0.5, 1.5))
                    break
            else:
                save_market_diagnostic(window, "precheck_missing_" + Path(filename).stem)
                break
        else:
            time.sleep(random.uniform(0.5, 0.8))
            screenshot = cv2.cvtColor(
                np.array(pyautogui.screenshot(region=window)), cv2.COLOR_RGB2BGR
            )
            occupied = len(find_baitan_slots(screenshot))
            remaining = max(0, 8 - occupied)
            print(f"Window {index}: precheck {occupied}/8 occupied, {remaining} to create.")

            # Close this marketplace once before phase 1 opens the huoli panel.
            time.sleep(random.uniform(0.5, 0.8))
            close, _ = find_icon_on_screen(market_close_path, screen_area=window)
            if close is None:
                save_market_diagnostic(window, "precheck_close_missing")
                continue
            random_click_mouse(close)
            time.sleep(random.uniform(0.5, 1.5))
            slots_left[tuple(window)] = remaining
    return slots_left


def utilize_huoli_method_1(slots_left):
    if not Path(TEMPLATE_PATH).is_file():
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

    for index, window in enumerate(window_capture_areas_, start=1):
        click_count = slots_left.get(tuple(window), 0)
        if click_count <= 0:
            print(f"Window {index}: full stall or unavailable precheck; skipping creation.")
            continue
        print(f"Window {index}: opening huoli panel.")
        random_click_mouse(offset_area(OPEN_AREA, window))
        time.sleep(random.uniform(2.0, 3.0))

        for attempt in range(TEMPLATE_ATTEMPTS):
            time.sleep(random.uniform(0.5, 0.8))
            match, _ = find_icon_on_screen(
                TEMPLATE_PATH, screen_area=window, threshold=0.8
            )
            if match is not None:
                break
            if attempt < TEMPLATE_ATTEMPTS - 1:
                time.sleep(0.5)
        else:
            print(f"Window {index}: huoli_utilize.png not found; skipping.")
            continue

        # Template matches already include the window's screen offset.
        random_click_mouse(match)
        time.sleep(random.uniform(2.0, 3.0))

        use_area = offset_area(USE_AREA, window)
        time.sleep(random.uniform(2.0, 3.0))
        for _ in range(click_count):
            random_click_mouse(use_area)
        print(f"Window {index}: completed {click_count} use clicks.")

        time.sleep(random.uniform(0.5, 0.8))
        match, _ = find_icon_on_screen(
            resource_path("img_templates", "party_panel_close.png"),
            # Restrict matching to the front huoli panel's close button.
            screen_area=(window[0] + 514, window[1] + 88, 44, 44),
        )
        if match is not None:
            random_click_mouse(match)
            time.sleep(random.uniform(2.0, 3.0))

        time.sleep(random.uniform(0.5, 0.8))
        match, _ = find_icon_on_screen(
            resource_path("img_templates", "market_close.png"),
            screen_area=(window[0] + 552, window[1] + 78, 44, 44),
        )
        if match is not None:
            random_click_mouse(match)
            time.sleep(random.uniform(2.0, 3.0))


BEIJING_TZ = timezone(timedelta(hours=8))
PHASE1_METHOD_OVERRIDE = None  # Set to 2 only for temporary testing.


def phase1_method(now=None):
    """Choose once at phase start: method 2 during [21:30, 08:00) Beijing time."""
    if PHASE1_METHOD_OVERRIDE is not None:
        return PHASE1_METHOD_OVERRIDE
    now = datetime.now(BEIJING_TZ) if now is None else now.astimezone(BEIJING_TZ)
    minutes = now.hour * 60 + now.minute
    return 2 if minutes >= 21 * 60 + 30 or minutes < 8 * 60 else 1


def find_phase1_template(filename, window):
    time.sleep(random.uniform(0.5, 0.8))
    match, _ = find_icon_on_screen(
        resource_path("img_templates", filename), screen_area=window, threshold=0.8
    )
    return match


def utilize_huoli_method_2(slots_left):
    templates = ("expand_bottom.png", "skill_panel.png", "huolifu_1.png",
                 "huolifu_2.png", "huolifu_3.png", "huolifu_zhizuo.PNG")
    for filename in templates:
        path = resource_path("img_templates", filename)
        if not Path(path).is_file():
            raise FileNotFoundError(f"Method 2 template missing: {path}")

    for index, window in enumerate(window_capture_areas_, start=1):
        click_count = slots_left.get(tuple(window), 0)
        if click_count <= 0:
            continue
        expand = find_phase1_template(templates[0], window)
        if expand is None:
            save_market_diagnostic(window, "method2_expand_missing")
            continue
        random_click_mouse(expand)
        # Clear the expand button's hover popup before looking for the skill icon.
        hover_x = window[0] + random.randint(280, 320)
        hover_y = window[1] + random.randint(330, 370)
        validate_click_area((hover_x, hover_y, hover_x, hover_y))
        move_mouse_smooth(hover_x, hover_y, duration=random.uniform(0.2, 0.4))
        time.sleep(random.uniform(0.5, 1.5))

        skill = find_phase1_template("skill_panel.png", window)
        if skill is None:
            save_market_diagnostic(window, "method2_skill_missing")
            continue
        hold_skill_button(skill)
        time.sleep(random.uniform(0.5, 1.5))

        for filename in ("huolifu_1.png", "huolifu_2.png", "huolifu_3.png"):
            glyph = find_phase1_template(filename, window)
            if glyph is not None:
                random_click_mouse(glyph)
                time.sleep(random.uniform(0.5, 1.5))
                break
        else:
            save_market_diagnostic(window, "method2_glyph_missing")
            continue

        completed = 0
        for _ in range(click_count):
            create = find_phase1_template("huolifu_zhizuo.PNG", window)
            if create is None:
                save_market_diagnostic(window, "method2_create_missing")
                break
            random_click_mouse(create)
            completed += 1
            time.sleep(random.uniform(0.5, 1.5))
        print(f"Window {index}: method 2 completed {completed}/{click_count} creation clicks.")

        close = find_phase1_template("market_close.png", window)
        if close is not None:
            random_click_mouse(close)
            time.sleep(random.uniform(0.5, 1.5))
        else:
            save_market_diagnostic(window, "method2_close_missing")


def utilize_huoli(slots_left=None):
    if slots_left is None:
        slots_left = precheck_baitan_slots()
    method = phase1_method()
    selection = "testing override" if PHASE1_METHOD_OVERRIDE is not None else "Beijing schedule"
    print(f"Phase 1: using method {method} ({selection}).")
    if method == 2:
        utilize_huoli_method_2(slots_left)
    else:
        utilize_huoli_method_1(slots_left)
    return method


def set_market_price(window, ocr, price_cap=None):
    """Reach the lower of the reference and optional cap, or the step below."""
    reference = None
    target_level = None
    previous_price = None
    direction = None
    stepped_down = False
    for _ in range(101):
        for attempt in range(3):
            time.sleep(random.uniform(0.5, 0.8))
            screenshot = cv2.cvtColor(
                np.array(pyautogui.screenshot(region=window)), cv2.COLOR_RGB2BGR
            )
            pricing = analyze_baitan_pricing(screenshot, ocr=ocr)
            if pricing["target_reliable"] and pricing["reference_price"] is not None:
                break
            if attempt < 2:
                time.sleep(1.0)
        current = pricing["current_price"]
        level = pricing["level"]
        if (not pricing["target_reliable"] or current is None or current <= 0
                or pricing["reference_price"] is None):
            print("Price recognition failed; skipping sale.")
            save_market_diagnostic(window, "pricing_failed", pricing)
            return False
        if reference is None:
            reference = pricing["reference_price"]
            target_level = level
        if reference <= 0 or level != target_level or pricing["reference_price"] != reference:
            print("Level or top reference changed; skipping sale.")
            return False
        if previous_price is not None:
            if ((direction == "plus" and current <= previous_price)
                    or (direction == "minus" and current >= previous_price)):
                print("Price did not move as expected; skipping sale.")
                return False
        target_price = min(reference, price_cap) if price_cap is not None else reference
        if current == target_price or (stepped_down and current < target_price):
            print(f"Window {window[:2]}: verified price {current} <= {target_price} "
                  f"(reference={reference}, cap={price_cap}).")
            return True
        if _ == 100:
            break
        direction = "minus" if current > target_price else "plus"
        if direction == "minus":
            stepped_down = True
        button_path = resource_path(
            "img_templates",
            "price_decrease.png" if direction == "minus" else "price_increase.png",
        )
        time.sleep(random.uniform(0.5, 0.8))
        button, confidence = find_icon_on_screen(
            button_path, screen_area=window, threshold=0.85
        )
        if button is None:
            save_market_diagnostic(window, f"price_{direction}_button_missing", pricing)
            return False
        print(f"Window {window[:2]}: {direction} button at {button}, score={confidence}.")
        random_click_mouse(button)
        previous_price = current
        time.sleep(random.uniform(0.5, 1.5))
    print("Price adjustment limit reached; skipping sale.")
    return False


def inventory_to_marketplace(windows=None, price_cap=None):
    """Open inventories, select one glyph per window, price it, and list it."""
    if windows is None:
        windows = window_capture_areas_
    if not windows:
        return []
    ocr = _make_ocr()
    template_folder = resource_path("img_templates", "temporary_glyph_inventory")
    time.sleep(random.uniform(0.5, 0.8))
    inventory_clicks, _ = find_icon_each_window(inventory_path, screen_area=windows, threshold=0.85)
    opened_windows = []
    for window, match in zip(windows, inventory_clicks):
        if match is not None:
            random_click_mouse(match)
            opened_windows.append(window)
    time.sleep(random.uniform(0.5, 1.5))

    if not opened_windows:
        return []

    time.sleep(random.uniform(0.5, 0.8))
    arrange_clicks, vals = find_icon_each_window(
        inventory_arrange_path, screen_area=opened_windows, threshold=0.90
    )
    for window, match, val in zip(opened_windows, arrange_clicks, vals):
        if match is not None:
            logger.info(f"Window {window[:2]}: inventory arrange at {match} with {val}")
            random_click_mouse(match)
        else:
            logger.warning(f"Window {window[:2]}: inventory arrange button not found")
    time.sleep(random.uniform(0.5, 1.5))

    marketplace_windows = []
    time.sleep(random.uniform(0.5, 0.8))
    results = find_icons_one_per_window(template_folder, opened_windows)
    for match, confidence, filename in results:
        random_click_mouse(match)
        print(f"Clicked {filename} at {match} with confidence {confidence}.")
        time.sleep(random.uniform(0.5, 1.5))
        window = next(
            window for window in opened_windows
            if window[0] <= match[0] < window[0] + window[2]
            and window[1] <= match[1] < window[1] + window[3]
        )

        time.sleep(random.uniform(0.5, 0.8))
        match, _ = find_icon_on_screen(inventory_additional_options_path, screen_area=window)
        if match is None:
            continue
        random_click_mouse(match)
        time.sleep(random.uniform(0.5, 1.5))

        time.sleep(random.uniform(0.5, 0.8))
        match, _ = find_icon_on_screen(market_to_sell_path, screen_area=window)
        if match is None:
            continue
        random_click_mouse(match)
        time.sleep(random.uniform(0.5, 1.5))

        if not set_market_price(window, ocr, price_cap=price_cap):
            continue

        time.sleep(random.uniform(0.5, 0.8))
        match, _ = find_icon_on_screen(market_launch_path, screen_area=window)
        if match is None:
            save_market_diagnostic(window, "phase2_launch_missing")
            continue
        random_click_mouse(match)
        time.sleep(random.uniform(0.5, 1.5))

        time.sleep(random.uniform(0.5, 0.8))
        match, _ = find_icon_on_screen(confirm_seven_days_path, screen_area=window)
        if match is not None:
            random_click_mouse(match)
            time.sleep(random.uniform(0.5, 1.5))
            time.sleep(random.uniform(0.5, 0.8))
            match, _ = find_icon_on_screen(market_sell_confirm_path, screen_area=window)
            if match is not None:
                random_click_mouse(match)
                time.sleep(random.uniform(0.5, 1.5))
            else:
                continue
        marketplace_windows.append(window)
    return marketplace_windows


def launch_remaining_glyphs(windows=None, price_cap=None):
    """Price and list visible right-side glyphs until the eight slots are full."""
    if windows is None:
        windows = window_capture_areas_
    if not windows:
        return
    ocr = _make_ocr()
    template_folder = resource_path("img_templates", "temporary_glyph_sell")

    def occupied_slots(window):
        time.sleep(random.uniform(0.5, 0.8))
        screenshot = cv2.cvtColor(
            np.array(pyautogui.screenshot(region=window)), cv2.COLOR_RGB2BGR
        )
        return len(find_baitan_slots(screenshot))

    for window in windows:
        occupied = occupied_slots(window)
        remaining = max(0, 8 - occupied)
        print(f"Window {window[:2]}: {occupied}/8 slots occupied, {remaining} left.")
        left, top, width, height = window
        right_half = (left + width // 2, top, width - width // 2, height)
        for _ in range(remaining):
            # Take a fresh screenshot each time: inventory items can move after listing.
            time.sleep(random.uniform(0.5, 0.8))
            matches = find_icons_one_per_window(template_folder, [right_half])
            if not matches:
                save_market_diagnostic(window, "no_sell_template_match")
                break
            match, confidence, filename = matches[0]
            print(f"Window {window[:2]}: sell template {filename} at {match}, score={confidence}.")
            random_click_mouse(match)
            time.sleep(random.uniform(0.5, 1.5))
            if not set_market_price(window, ocr, price_cap=price_cap):
                break
            time.sleep(random.uniform(0.5, 0.8))
            launch, _ = find_icon_on_screen(market_launch_path, screen_area=window)
            if launch is None:
                save_market_diagnostic(window, "phase3_launch_missing")
                break
            random_click_mouse(launch)
            time.sleep(random.uniform(0.5, 1.5))

            updated_count = occupied_slots(window)
            if updated_count <= occupied:
                print(f"Window {window[:2]}: new listing not verified; stopping.")
                save_market_diagnostic(window, "listing_not_verified")
                break
            occupied = updated_count
            print(f"Window {window[:2]}: launched {filename}; {occupied}/8 slots occupied.")
            if occupied >= 8:
                break


def close_marketplace_and_inventory(windows=None):
    """Close the marketplace, then the inventory revealed behind it."""
    if windows is None:
        windows = window_capture_areas_
    if not windows:
        return
    time.sleep(random.uniform(0.5, 0.8))
    results, vals = find_icon_each_window(market_close_path, screen_area=windows)
    for result, val in zip(results, vals):
        if result is not None:
            logger.info(f"found market_close_path at {result} with {val}")
            random_click_mouse(result)
    time.sleep(random.uniform(0.5, 1.5))

    # Re-scan after closing the market to locate the inventory's red X.
    time.sleep(random.uniform(0.5, 0.8))
    results, vals = find_icon_each_window(market_close_path, screen_area=windows)
    for result, val in zip(results, vals):
        if result is not None:
            logger.info(f"found inventory close at {result} with {val}")
            random_click_mouse(result)


def huoli_sell():
    """Check stall capacity, create that many glyphs, and list them."""
    slots_left = precheck_baitan_slots()
    active_windows = [window for window in window_capture_areas_
                      if slots_left.get(tuple(window), 0) > 0]
    if not active_windows:
        return
    method = utilize_huoli(slots_left)
    price_cap = 180 if method == 2 else None
    marketplace_windows = inventory_to_marketplace(active_windows, price_cap=price_cap)
    launch_remaining_glyphs(marketplace_windows, price_cap=price_cap)
    close_marketplace_and_inventory(active_windows)


if __name__ == "__main__":
    huoli_sell()
