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

TARGET_ITEM_TEMPLATE_PATHS = [
    "img_templates/fabao_1.png",
    "img_templates/fabao_2.png",
    "img_templates/fabao_3.png",
    "img_templates/fabao_4.png",
    "img_templates/fabao_5.png",
    "img_templates/fabao_6.png",
    "img_templates/fabao_7.png",
]

STEP1_OFFSET_MS = 1700
STEP2_DELAY_MS = 300
STEP2_POST_CLICK_DELAY_MS = 150
BUY_SPAM_CLICKS = 30
TEST_MODE = False
TARGET_START_HOUR = 12
TARGET_START_MINUTE = 00
TARGET_START_SECOND = 00

BJ_TZ = ZoneInfo("Asia/Shanghai")


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


def main() -> None:
    templates = {
        "step1": load_template(STEP1_TEMPLATE_PATH),
        "step2": load_template(STEP2_TEMPLATE_PATH),
        "buy_button": load_template(BUY_BUTTON_TEMPLATE_PATH),
    }
    item_templates: List[Tuple[str, np.ndarray]] = [
        (path, load_template(path)) for path in TARGET_ITEM_TEMPLATE_PATHS
    ]

    bm.FAST_MODE = True

    now_bj = dt.datetime.now(BJ_TZ)
    print(f"[SCHEDULE] now(BJ):   {now_bj.isoformat()}")
    if TEST_MODE:
        print("[SCHEDULE] test mode: start immediately")
    else:
        target_bj = next_target_time(now_bj)
        step1_bj = target_bj + dt.timedelta(milliseconds=STEP1_OFFSET_MS)
        print(f"[SCHEDULE] target(BJ): {target_bj.isoformat()}")
        print(f"[SCHEDULE] step1(BJ): {step1_bj.isoformat()}")
        print(f"[SCHEDULE] step2 delay: {STEP2_DELAY_MS}ms after step1")
        wait_until_epoch(step1_bj.timestamp())

    click_template("step1", templates["step1"], MATCH_THRESHOLD)

    if STEP2_DELAY_MS > 0:
        time.sleep(STEP2_DELAY_MS / 1000.0)

    step2_xy = click_template("step2", templates["step2"], MATCH_THRESHOLD, retry_until_found=True)
    if step2_xy is not None and STEP2_POST_CLICK_DELAY_MS > 0:
        time.sleep(STEP2_POST_CLICK_DELAY_MS / 1000.0)

    sale_img = capture_screen()
    selected_item_xy = None
    selected_item_name = None
    item_scores = []
    for item_path, item_tpl in item_templates:
        item_score = match_value_in_master(sale_img, item_tpl)
        item_scores.append((item_path, item_score, item_tpl))

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


if __name__ == "__main__":
    main()
