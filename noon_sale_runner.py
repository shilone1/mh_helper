import _thread
import datetime as dt
import random
import time
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo

import cv2
import numpy as np
import pyautogui

import broadcast_mouse as bm

MASTER_WINDOW_INDEX = 0
MATCH_THRESHOLD = 0.80
ITEM_MATCH_THRESHOLD = 0.50

STEP1_TEMPLATE_PATH = "img_templates/fabao_runner_01.png"
STEP2_TEMPLATE_PATH = "img_templates/fabao_runner_02.png"
BUY_BUTTON_TEMPLATE_PATH = "img_templates/fabao_purchase.png"
CLOSE_BUTTON_TEMPLATE_PATH = "img_templates/party_panel_close.png"

TARGET_ITEM_TEMPLATE_PATHS = [
    "img_templates/fabao_1.png",
    "img_templates/fabao_2.png",
    "img_templates/fabao_3.png",
    "img_templates/fabao_4.png",
    "img_templates/fabao_5.png",
    "img_templates/fabao_6.png",
    "img_templates/fabao_7.png",
]

STEP1_OFFSET_MS = 1200
STEP2_DELAY_MS = 300
STEP2_POST_CLICK_DELAY_MS = 150
BUY_SPAM_CLICKS = 30
# Temporary dry run: skip clock waits and stop before any purchase-phase clicks.
TEST_MODE = False
TARGET_START_HOUR = 12
TARGET_START_MINUTE = 00
TARGET_START_SECOND = 00

BJ_TZ = ZoneInfo("Asia/Shanghai")
PREVIEW_MINUTES_BEFORE = 5
PREVIEW_SETTLE_SECONDS = 0.75
UI_POLL_SECONDS = 0.02
UI_TIMEOUT_SECONDS = 10.0
# Icon interiors relative to the matched close template's top-left corner.
# Excludes names, prices, selection borders, and the quantity controls.
SALE_ICON_OFFSETS = [(x, y, 34, 32) for y in (85, 141, 197) for x in (-477, -321)]
ICON_SAME_THRESHOLD = 0.90


def next_target_time(now_bj: dt.datetime) -> dt.datetime:
    target = now_bj.replace(
        hour=TARGET_START_HOUR,
        minute=TARGET_START_MINUTE,
        second=TARGET_START_SECOND,
        microsecond=0,
    )
    if now_bj >= target:
        target += dt.timedelta(days=1)
    return target


def wait_until_epoch(target_epoch: float) -> None:
    while True:
        remaining = target_epoch - time.time()
        if remaining <= 0:
            return
        if remaining > 1.0:
            time.sleep(remaining - 0.5)
        elif remaining > 0.05:
            time.sleep(remaining - 0.02)
        else:
            time.sleep(0)


def load_template(path: str) -> np.ndarray:
    tpl = cv2.imread(path, cv2.IMREAD_COLOR)
    if tpl is None:
        raise FileNotFoundError(f"Template not found or unreadable: {path}")
    return tpl


def capture_screen() -> np.ndarray:
    wx, wy, ww, wh = bm.window_capture_areas_[MASTER_WINDOW_INDEX]
    shot = pyautogui.screenshot(region=(wx, wy, ww, wh))
    return cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)


def match_center_in_master(
    master_img: np.ndarray,
    template: np.ndarray,
    threshold: float,
) -> Optional[Tuple[int, int]]:
    wx, wy, ww, wh = bm.window_capture_areas_[MASTER_WINDOW_INDEX]
    res = cv2.matchTemplate(master_img, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val < threshold:
        return None

    th, tw = template.shape[:2]
    jitter_x = random.randint(max(0, tw // 4), max(0, (3 * tw) // 4))
    jitter_y = random.randint(max(0, th // 4), max(0, (3 * th) // 4))
    center_x = wx + max_loc[0] + jitter_x
    center_y = wy + max_loc[1] + jitter_y
    center_x = min(max(center_x, wx), wx + ww - 1)
    center_y = min(max(center_y, wy), wy + wh - 1)
    return center_x, center_y


def match_value_in_master(master_img: np.ndarray, template: np.ndarray) -> float:
    res = cv2.matchTemplate(master_img, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    return float(max_val)


def click_template(
    label: str,
    template: np.ndarray,
    threshold: float,
    retry_until_found: bool = False,
) -> Optional[Tuple[int, int]]:
    while True:
        point = match_center_in_master(capture_screen(), template, threshold)
        if point is not None:
            click_point(point[0], point[1], label)
            return point

        print(f"[MISS] {label}")
        if not retry_until_found:
            return None
        time.sleep(0.02)


def click_point(x: int, y: int, label: str) -> None:
    bm.click_master_and_children(x, y, "left")
    print(f"[CLICK] {label} at ({x},{y})")


def spam_click_point(x: int, y: int, label: str, count: int) -> None:
    for _ in range(count):
        bm.click_master_and_children(x, y, "left")
        time.sleep(random.uniform(0.01, 0.05))
    print(f"[SPAM] {label} x{count} at ({x},{y})")


def wait_for_template(label, template):
    deadline = time.monotonic() + UI_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        shot = capture_screen()
        point = match_center_in_master(shot, template, MATCH_THRESHOLD)
        if point is not None:
            return shot, point
        time.sleep(UI_POLL_SECONDS)
    raise RuntimeError(f"Timed out waiting for {label}")


def open_sale(templates, preview=False):
    _, point = wait_for_template("step1", templates["step1"])
    click_point(*point, "step1")
    time.sleep(PREVIEW_SETTLE_SECONDS if preview else STEP2_DELAY_MS / 1000.0)
    _, point = wait_for_template("step2", templates["step2"])
    click_point(*point, "step2")
    time.sleep(PREVIEW_SETTLE_SECONDS if preview else STEP2_POST_CLICK_DELAY_MS / 1000.0)


def read_sale(templates):
    # A missing/loading page must never be interpreted as changed inventory.
    deadline = time.monotonic() + UI_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        shot = capture_screen()
        if match_value_in_master(shot, templates["buy_button"]) >= MATCH_THRESHOLD:
            result = cv2.matchTemplate(shot, templates["close"], cv2.TM_CCOEFF_NORMED)
            _, confidence, _, (anchor_x, anchor_y) = cv2.minMaxLoc(result)
            if confidence >= MATCH_THRESHOLD:
                icons = []
                for dx, dy, width, height in SALE_ICON_OFFSETS:
                    x, y = anchor_x + dx, anchor_y + dy
                    icon = shot[y:y + height, x:x + width]
                    if x < 0 or y < 0 or icon.shape[:2] != (height, width):
                        raise RuntimeError("Sale icon region is outside the captured window")
                    icons.append(icon.copy())
                return shot, icons
        time.sleep(UI_POLL_SECONDS)
    raise RuntimeError("Sale page did not load; stopping")


def same_fabao_kinds(remembered_icons, current_icons):
    """Only an unchanged complete list should trigger a refresh retry."""
    return (len(remembered_icons) == len(current_icons)
            and all(match_value_in_master(current, remembered) >= ICON_SAME_THRESHOLD
                    for remembered, current in zip(remembered_icons, current_icons)))


def close_sale(templates):
    shot = capture_screen()
    result = cv2.matchTemplate(shot, templates["buy_button"], cv2.TM_CCOEFF_NORMED)
    _, confidence, _, (buy_x, buy_y) = cv2.minMaxLoc(result)
    if confidence < MATCH_THRESHOLD:
        raise RuntimeError("Sale page is not visible; refusing to close another menu")

    # Anchor to the purchase button; the tab changes appearance when selected.
    # Search only this sale panel's own top-right X.
    x, y = buy_x + 134, buy_y - 295
    close_region = shot[y:y + 40, x:x + 50]
    if x < 0 or y < 0 or close_region.shape[:2] != (40, 50):
        raise RuntimeError("Sale close-button region is outside the captured window")
    result = cv2.matchTemplate(close_region, templates["close"], cv2.TM_CCOEFF_NORMED)
    _, confidence, _, (close_x, close_y) = cv2.minMaxLoc(result)
    if confidence < MATCH_THRESHOLD:
        raise RuntimeError("Sale panel close button was not found")
    th, tw = templates["close"].shape[:2]
    wx, wy, _, _ = bm.window_capture_areas_[MASTER_WINDOW_INDEX]
    click_point(wx + x + close_x + tw // 2, wy + y + close_y + th // 2, "sale_close")

    # One broadcast only. Other menus may use the same X template.
    # Polling for readiness must never click their close buttons.
    wait_for_template("step1 after closing sale", templates["step1"])


def wait_for_changed_sale(templates, remembered_icons):
    attempts = 0
    while True:
        open_sale(templates)
        sale_img, icons = read_sale(templates)
        if not same_fabao_kinds(remembered_icons, icons):
            # Confirm a stable new inventory rather than a partially drawn frame.
            time.sleep(UI_POLL_SECONDS)
            sale_img, confirmed_icons = read_sale(templates)
            if (same_fabao_kinds(icons, confirmed_icons)
                    and not same_fabao_kinds(remembered_icons, confirmed_icons)):
                print(f"[REFRESH] fabao kinds changed after {attempts} retries")
                return sale_img
        attempts += 1
        print(f"[REFRESH] unchanged fabao; fast retry {attempts}")
        close_sale(templates)


def main() -> None:
    templates = {
        "step1": load_template(STEP1_TEMPLATE_PATH),
        "step2": load_template(STEP2_TEMPLATE_PATH),
        "buy_button": load_template(BUY_BUTTON_TEMPLATE_PATH),
        "close": load_template(CLOSE_BUTTON_TEMPLATE_PATH),
    }
    item_templates: List[Tuple[str, np.ndarray]] = [
        (path, load_template(path)) for path in TARGET_ITEM_TEMPLATE_PATHS
    ]

    bm.FAST_MODE = True

    now_bj = dt.datetime.now(BJ_TZ)
    print(f"[SCHEDULE] now(BJ):   {now_bj.isoformat()}")
    if TEST_MODE:
        print("[TEST] snapshot and execution immediately; purchasing DISABLED")
        print("[TEST] unchanged stock keeps retrying; press Ctrl+C to stop")
        step1_bj = None
    else:
        target_bj = next_target_time(now_bj)
        step1_bj = target_bj + dt.timedelta(milliseconds=STEP1_OFFSET_MS)
        print(f"[SCHEDULE] target(BJ): {target_bj.isoformat()}")
        print(f"[SCHEDULE] step1(BJ): {step1_bj.isoformat()}")
        print(f"[SCHEDULE] step2 delay: {STEP2_DELAY_MS}ms after step1")
        preview_bj = target_bj - dt.timedelta(minutes=PREVIEW_MINUTES_BEFORE)
        print(f"[SCHEDULE] snapshot(BJ): {preview_bj.isoformat()}")
        if now_bj > preview_bj:
            print("[SCHEDULE] snapshot time passed; taking snapshot immediately")
        wait_until_epoch(preview_bj.timestamp())

    open_sale(templates, preview=True)
    _, remembered_icons = read_sale(templates)
    print(f"[SNAPSHOT] remembered {len(remembered_icons)} sale icon images")
    close_sale(templates)

    if step1_bj is not None:
        if time.time() >= step1_bj.timestamp():
            raise RuntimeError("Snapshot finished after execution time; restart before the next sale")
        wait_until_epoch(step1_bj.timestamp())

    sale_img = wait_for_changed_sale(templates, remembered_icons)
    if TEST_MODE:
        print("[TEST] changed stock confirmed; staying on sale page, no purchase clicks")
        return

    item_scores = [(path, match_value_in_master(sale_img, tpl), tpl)
                   for path, tpl in item_templates]
    selected_item_xy = None
    selected_item_name = None

    score_lines = [
        f"[ITEM] {item_path} score={item_score:.4f}"
        for item_path, item_score, _ in item_scores
    ]
    print("\n".join(score_lines))

    for item_path, _, item_tpl in item_scores:
        item_xy = match_center_in_master(sale_img, item_tpl, ITEM_MATCH_THRESHOLD)
        if item_xy is None:
            continue
        selected_item_xy = item_xy
        selected_item_name = item_path
        break

    if selected_item_xy is not None:
        click_point(selected_item_xy[0], selected_item_xy[1], f"item:{selected_item_name}")
        time.sleep(0.005)
        buy_xy = click_template("buy_button", templates["buy_button"], MATCH_THRESHOLD)
        if buy_xy is not None:
            spam_click_point(buy_xy[0], buy_xy[1], "buy_button_spam", BUY_SPAM_CLICKS - 1)
    else:
        print("[MISS] no prioritized item template matched on sale page")

    print("[DONE] noon sale flow finished")


def on_stop_key(key):
    if key == bm.keyboard.Key.f8:
        bm.stop_event.set()
        _thread.interrupt_main()
        return False


def run() -> None:
    print("[STOP] Press F8 from any window to stop (Ctrl+C also works in the terminal)")
    try:
        with bm.keyboard.Listener(on_press=on_stop_key):
            main()
    except KeyboardInterrupt:
        print("\n[STOP] noon sale runner stopped")
    finally:
        bm.stop_event.set()


if __name__ == "__main__":
    run()
