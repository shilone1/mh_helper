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
    window_capture_areas_, market_launch_path, confirm_seven_days_path,
    market_sell_confirm_path, market_close_path,
)
from image_matching import find_icon_on_screen, find_icon_each_window, find_icons_one_per_window
from mouse_action import random_click_mouse as _random_click_mouse
from mouse_action import hold_left_mouse_button, release_left_mouse_button, move_mouse_smooth
from slot_detection import find_baitan_slots
from logger import logger
from market_verification import (poll_listing, recover_pricing, template_scores,
                                 market_visible)


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


def save_market_diagnostic(window, reason, pricing=None, before=None, after=None):
    folder = Path(resource_path("pricing_diagnostics"))
    folder.mkdir(exist_ok=True)
    name = f"window_{window[0]}_{window[1]}_{time.time_ns()}_{reason}"
    if after is None:
        after = capture_market(window)
    cv2.imwrite(str(folder / (name + ".png")), after)
    if before is not None:
        cv2.imwrite(str(folder / (name + "_before.png")), before)
    if pricing is not None:
        (folder / (name + ".json")).write_text(
            json.dumps(pricing, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(f"Window {window[:2]}: {reason}; saved {folder / name}", flush=True)


def capture_market(window):
    return cv2.cvtColor(np.array(pyautogui.screenshot(region=window)), cv2.COLOR_RGB2BGR)


def clear_market_hover(window):
    """Clear tooltips by moving to a random point in the bottom-center area."""
    x = window[0] + random.randint(290, 330)
    y = window[1] + random.randint(430, 450)
    validate_click_area((x, y, x, y))
    move_mouse_smooth(x, y, duration=.2)


def dismiss_market_event_popup(window):
    """Close the event notification if it is obstructing a pricing retry."""
    close, confidence = find_icon_on_screen(
        resource_path("img_templates", "event_popup_close.png"),
        screen_area=window, threshold=0.90,
    )
    if close is None:
        return False
    # Keep the click inside the circular button, away from the event banner.
    x1, y1, x2, y2 = close
    random_click_mouse((x1 + 7, y1 + 7, x2 - 7, y2 - 7))
    print(f"Window {window[:2]}: closed event popup before pricing retry, "
          f"score={confidence}.")
    return True


def offset_area(area, window):
    """Translate a local click rectangle using the window's left/top origin."""
    left, top = window[:2]
    x1, y1, x2, y2 = area
    return (left + x1, top + y1, left + x2, top + y2)


def open_baitan_sell(window, phase):
    """Shared phase 0/2 route: shop -> stall -> sell tab, resuming where visible."""
    sell_path = resource_path("img_templates", "want_to_chushou.png")
    for filename in ("shangcheng.png", "baitan.png", "want_to_chushou.png"):
        for attempt in range(TEMPLATE_ATTEMPTS):
            time.sleep(random.uniform(.5, .8))
            # Check before every navigation click, including retries: opening
            # the shop may restore the stall directly instead of its home page.
            sell, _ = find_icon_on_screen(sell_path, screen_area=window)
            if sell is not None:
                random_click_mouse(sell)
                for _ in range(TEMPLATE_ATTEMPTS):
                    time.sleep(.5)
                    if market_visible(capture_market(window)):
                        return True
                save_market_diagnostic(window, phase + "_sell_view_not_ready")
                return False
            if filename == "want_to_chushou.png":
                continue
            match, _ = find_icon_on_screen(
                resource_path("img_templates", filename), screen_area=window)
            if match is not None:
                random_click_mouse(match)
                time.sleep(random.uniform(.5, 1.5))
                break
        else:
            save_market_diagnostic(window, phase + "_missing_" + Path(filename).stem)
            return False
    return False


def precheck_baitan_slots():
    """Return free slots by window; omit windows whose navigation failed."""
    slots_left = {}
    for index, window in enumerate(window_capture_areas_, start=1):
        if not open_baitan_sell(window, "precheck"):
            continue
        occupied = len(find_baitan_slots(capture_market(window)))
        remaining = max(0, 8 - occupied)
        print(f"Window {index}: precheck {occupied}/8 occupied, {remaining} to create.")
        close, _ = find_icon_on_screen(market_close_path, screen_area=window)
        if close is None:
            save_market_diagnostic(window, "precheck_close_missing")
            continue
        random_click_mouse(close)
        time.sleep(random.uniform(.5, 1.5))
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


def set_market_price(window, ocr, price_cap=None, readings=None):
    """Match the reference/cap, or keep the current price when listings are empty."""
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
            if (reference is None and pricing["target_reliable"]
                    and pricing["current_price"] is not None
                    and pricing["current_price"] > 0
                    and pricing["reference_price"] is None
                    and pricing.get("listings") == []):
                if readings is not None:
                    readings.append(pricing)
                print(f"Window {window[:2]}: no comparison listings; "
                      f"keeping current price {pricing['current_price']}.")
                return True
            if pricing["target_reliable"] and pricing["reference_price"] is not None:
                break
            if attempt < 2:
                dismiss_market_event_popup(window)
                clear_market_hover(window)
                time.sleep(1.0)
        current = pricing["current_price"]
        if not pricing["target_reliable"] or pricing["reference_price"] is None:
            pricing = recover_pricing(screenshot, ocr, pricing)
            current = pricing["current_price"]
            if pricing["recovery_accepted"]:
                print(f"Window {window[:2]}: OCR recovered by agreeing variants; "
                      f"level={pricing['level']}, price={current}, "
                      f"reference={pricing['reference_price']}.")
        level = pricing["level"]
        if readings is not None:
            readings.append(pricing)
        if (not pricing["target_reliable"] or current is None or current <= 0
                or pricing["reference_price"] is None):
            print("Price recognition failed; skipping sale.")
            save_market_diagnostic(window, "pricing_failed", pricing, after=screenshot)
            return False
        if reference is None:
            reference = pricing["reference_price"]
            target_level = level
        if reference <= 0 or level != target_level or pricing["reference_price"] != reference:
            print("Level or top reference changed; skipping sale.")
            save_market_diagnostic(window, "pricing_reference_changed", pricing, after=screenshot)
            return False
        if previous_price is not None:
            if ((direction == "plus" and current <= previous_price)
                    or (direction == "minus" and current >= previous_price)):
                print("Price did not move as expected; skipping sale.")
                save_market_diagnostic(window, "pricing_did_not_move", pricing, after=screenshot)
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


def open_marketplaces(windows=None):
    """Phase 2: enter the selling view using the same navigation as phase 0."""
    windows = window_capture_areas_ if windows is None else windows
    return [window for window in windows if open_baitan_sell(window, "phase2")]


def confirm_listing_duration(window):
    """Handle the optional first-listing duration prompt in the selling loop."""
    time.sleep(.5)
    duration, _ = find_icon_on_screen(confirm_seven_days_path, screen_area=window)
    if duration is None:
        return True
    random_click_mouse(duration)
    for _ in range(TEMPLATE_ATTEMPTS):
        time.sleep(.5)
        confirm, _ = find_icon_on_screen(market_sell_confirm_path, screen_area=window)
        if confirm is not None:
            random_click_mouse(confirm)
            return True
    save_market_diagnostic(window, "listing_confirmation_missing")
    return False


def launch_remaining_glyphs(windows=None, price_cap=None):
    """List with bounded retries and evidence from stable market screenshots."""
    windows = window_capture_areas_ if windows is None else windows
    summaries = {}
    if not windows:
        return summaries
    ocr = _make_ocr()
    folder = resource_path("img_templates", "temporary_glyph_sell")
    for window in windows:
        time.sleep(.5)
        before = capture_market(window)
        if not market_visible(before):
            save_market_diagnostic(window, "market_not_visible", after=before)
            summaries[tuple(window)] = {"occupied": None, "reason": "market_not_visible"}
            continue
        occupied = len(find_baitan_slots(before))
        remaining = max(0, 8 - occupied)
        reason = "full" if remaining == 0 else "attempt_limit"
        print(f"Window {window[:2]}: {occupied}/8 slots occupied, {remaining} left.")
        left, top, width, height = window
        right_half = (left + width // 2, top, width - width // 2, height)
        # Limit successful operations even when other listings sell during the run.
        for _ in range(remaining):
            for retry in range(2):
                time.sleep(.5)
                before = capture_market(window)
                if not market_visible(before):
                    reason = "market_not_visible"
                    save_market_diagnostic(window, reason, after=before)
                    break
                occupied = len(find_baitan_slots(before))
                if occupied >= 8:
                    reason = "full"
                    break
                score_history = []
                for scan in range(3):
                    matches = find_icons_one_per_window(folder, [right_half])
                    if matches:
                        break
                    score_history.append(template_scores(capture_market(window)))
                    if scan < 2:
                        clear_market_hover(window)
                        time.sleep(.75)
                if not matches:
                    reason = "no_sell_template_match"
                    save_market_diagnostic(window, reason, {"scores": score_history}, before=before)
                    break
                match, confidence, filename = matches[0]
                # Capture the inventory before opening the price dialog.
                before = capture_market(window)
                occupied = len(find_baitan_slots(before))
                select_click = random_click_mouse(match)
                print(f"Window {window[:2]}: sell template {filename} at {match}, score={confidence}.")
                time.sleep(random.uniform(.5, 1.5))
                pricing_readings = []
                if not set_market_price(window, ocr, price_cap=price_cap, readings=pricing_readings):
                    reason = "pricing_failed"
                    break
                launch, _ = find_icon_on_screen(market_launch_path, screen_area=window)
                if launch is None:
                    reason = "phase3_launch_missing"
                    save_market_diagnostic(window, reason, before=before)
                    break
                price_dialog = capture_market(window)
                launch_click = random_click_mouse(launch)
                if not confirm_listing_duration(window):
                    reason = "listing_confirmation_missing"
                    break
                outcome, after, history = poll_listing(
                    before, filename, occupied, lambda: capture_market(window))
                details = {"previous_count": occupied, "template": filename,
                           "template_confidence": confidence, "select_click": select_click,
                           "launch_click": launch_click, "retry": retry, "observations": history,
                           "pricing_readings": pricing_readings}
                if outcome in ("listed", "inventory_decreased"):
                    occupied = history[-1]["occupied"]
                    print(f"Window {window[:2]}: {outcome}; {occupied}/8 slots occupied.")
                    reason = "full" if occupied >= 8 else "attempt_limit"
                    break
                reason = "listing_unchanged" if outcome == "unchanged" else "listing_ambiguous"
                save_market_diagnostic(window, reason, details, before=before, after=after)
                save_market_diagnostic(window, "listing_price_dialog", details, after=price_dialog)
                if outcome != "unchanged" or retry == 1:
                    break
                print(f"Window {window[:2]}: inventory and count unchanged; reopening and retrying once.")
            if reason != "attempt_limit":
                break
        summaries[tuple(window)] = {"occupied": occupied, "reason": reason}
    return summaries


def close_marketplace_and_inventory(windows=None):
    """Close any remaining price dialog and marketplace panels."""
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

    # A failed price dialog can leave the main marketplace behind it.
    time.sleep(random.uniform(0.5, 0.8))
    results, vals = find_icon_each_window(market_close_path, screen_area=windows)
    for result, val in zip(results, vals):
        if result is not None:
            logger.info(f"found remaining panel close at {result} with {val}")
            random_click_mouse(result)


def huoli_sell():
    """Check stall capacity, create that many glyphs, and list them."""
    slots_left = precheck_baitan_slots()
    active_windows = [window for window in window_capture_areas_
                      if slots_left.get(tuple(window), 0) > 0]
    summaries = {}
    if active_windows:
        method = utilize_huoli(slots_left)
        price_cap = 180 if method == 2 else None
        marketplace_windows = open_marketplaces(active_windows)
        summaries = launch_remaining_glyphs(marketplace_windows, price_cap=price_cap)
        close_marketplace_and_inventory(active_windows)
    for index, window in enumerate(window_capture_areas_, 1):
        key = tuple(window)
        default = ({"occupied": 8, "reason": "already_full"} if slots_left.get(key) == 0
                   else {"occupied": None, "reason": "phase2_incomplete" if key in slots_left
                         else "precheck_failed"})
        result = summaries.setdefault(key, default)
        count = result["occupied"]
        print(f"Window {index} {window[:2]}: final observed count "
              f"{count if count is not None else 'unknown'}/8; {result['reason']}.")
    return summaries


if __name__ == "__main__":
    huoli_sell()
