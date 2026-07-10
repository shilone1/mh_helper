import os
import json
import time
import re
from difflib import SequenceMatcher
import cv2
import numpy as np
import pyautogui
from paddleocr import PaddleOCR

from mouse_action import random_click_mouse
import image_matching as im
from config import *

JSON_PATH = "qiyuan_table.json"
QIYUAN_DIR = "img_templates/qiyuan_templates"          # folder on disk
QIYUAN_PREFIX = "img_templates/qiyuan_templates"       # stored into json

# ---------- regex for question extraction ----------
ROUND_PAT = re.compile(r"[（(【\[]\s*\d+\s*/\s*\d+\s*[】\])）\]]|\b\d+\s*/\s*\d+\b")
CN_SPACE_PAT = re.compile(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])")
PUNCT_SPACE_PAT = re.compile(r"[\s：:，,。．.!！?？;；、'\"“”‘’()（）【】\[\]《》<>·…-]+")


# =========================
# JSON load/save
# =========================
def load_table(path: str) -> dict:
    if not os.path.exists(path):
        return {"questions": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_table(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_question_for_match(text: str) -> str:
    """Normalize OCR text for tolerant matching."""
    t = (text or "").strip().lower()
    t = CN_SPACE_PAT.sub("", t)
    t = PUNCT_SPACE_PAT.sub("", t)
    return t


def resolve_similar_question_key(question: str, qmap: dict, min_ratio: float = 0.86) -> str | None:
    """
    Return the best existing key when OCR text is very similar.
    """
    if question in qmap:
        return question

    qn = normalize_question_for_match(question)
    if not qn:
        return None

    best_ratio_key = None
    best_ratio = 0.0
    best_overlap_key = None
    best_overlap = 0

    for key in qmap.keys():
        kn = normalize_question_for_match(key)
        if not kn:
            continue
        if kn == qn:
            return key

        if qn in kn or kn in qn:
            overlap = min(len(qn), len(kn))
            if overlap > best_overlap:
                best_overlap = overlap
                best_overlap_key = key

        ratio = SequenceMatcher(None, qn, kn).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_ratio_key = key

    # Truncated OCR line still passes if overlap is strong enough.
    if best_overlap >= 10:
        return best_overlap_key

    # For short text, require stricter ratio to avoid false positives.
    dynamic_ratio = 0.92 if len(qn) < 10 else min_ratio
    if best_ratio >= dynamic_ratio:
        return best_ratio_key
    return None


# =========================
# Extract question: ONLY the single OCR entry that contains "第n题"
# =========================
def extract_question(ocr_result, min_conf=0.50) -> str | None:
    """
    Find the single OCR entry that contains '第n题'.
    Return only the text after '第n题', with (x/y) removed if present.
    """
    if not ocr_result or not ocr_result[0]:
        return None

    best = None  # (conf, tail)
    for _box, (text, conf) in ocr_result[0]:
        if not text:
            continue
        t = text.strip()
        if conf < min_conf:
            continue

        m = re.search(r"第\s*\d+\s*题\s*[:：]?\s*(.*)", t)
        if not m:
            continue

        tail = m.group(1).strip()
        tail = ROUND_PAT.sub("", tail)
        tail = re.sub(r"\s+", " ", tail).strip()
        tail = CN_SPACE_PAT.sub("", tail)
        tail = tail.strip(" ：:，,。．. ")

        if not tail:
            continue

        if best is None or float(conf) > best[0]:
            best = (float(conf), tail)

    return best[1] if best else None


# =========================
# Flatten images from json entry
# json schema:
#  { "rounds": [ [p1,p2], [p3] ] }
# We'll just iterate ALL images until question changes.
# =========================
def get_image_list(entry: dict) -> list[str]:
    rounds = entry.get("rounds", [])
    out = []
    for r in rounds:
        if isinstance(r, list):
            out.extend(r)
    return out


# =========================
# Click logic: try any template, click first match
# =========================
def try_click_any(images: list[str], screen_area) -> bool:
    for p in images:
        # keep path as stored in json
        res, score = im.find_icon_on_screen(p, screen_area=screen_area)
        if res:
            random_click_mouse(res)
            return True
    return False


# =========================
# Record mode helpers
# =========================
def get_next_question_id() -> int:
    """
    Scan QIYUAN_DIR for files like '6_1.png' and return next id (max+1).
    """
    os.makedirs(QIYUAN_DIR, exist_ok=True)
    max_id = 0
    pat = re.compile(r"^(\d+)_\d+\.png$", re.IGNORECASE)

    for fn in os.listdir(QIYUAN_DIR):
        m = pat.match(fn)
        if not m:
            continue
        n = int(m.group(1))
        if n > max_id:
            max_id = n

    return max_id + 1


def read_key_blocking():
    """
    Windows: use msvcrt to read a key without Enter.
    Returns: '1'/'2'/'3'/'ENTER'/None
    """
    try:
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("1", "2", "3"):
            return ch
        if ch == "\r":
            return "ENTER"
        return None
    except Exception:
        s = input().strip()
        if s in ("1", "2", "3"):
            return s
        if s == "":
            return "ENTER"
        return None


def clear_key_buffer():
    try:
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getwch()
    except Exception:
        pass


def record_mode_add_images(table: dict, question: str) -> None:
    """
    Append templates for THIS question.
    Press 1/2/3 to capture option slot 1/2/3 (fixed regions).
    Press ENTER to finish.
    Images are appended to entry["rounds"][0] (single list).
    """
    qmap = table.setdefault("questions", {})
    if question not in qmap:
        qmap[question] = {"rounds": [[]]}

    entry = qmap[question]
    entry.setdefault("rounds", [[]])
    if not entry["rounds"]:
        entry["rounds"] = [[]]

    qid = get_next_question_id()
    capture_idx = 1

    print(f"\n[RECORD] Add templates for question:\n  {question}")
    print("[RECORD] Press 1/2/3 to capture option slot 1/2/3. Press ENTER to finish.")

    clear_key_buffer()

    while True:
        k = read_key_blocking()
        if k is None:
            continue

        if k == "ENTER":
            break

        if k not in ("1", "2", "3"):
            continue

        # NOTE: these are absolute screen coords (same as your current code).
        if k == "1":
            record_area = (225, 145, 100, 145)
        elif k == "2":
            record_area = (345, 145, 100, 145)
        else:
            record_area = (460, 145, 100, 145)

        fn = f"{qid}_{capture_idx}.png"
        capture_idx += 1

        save_abs = os.path.join(QIYUAN_DIR, fn)
        shot = pyautogui.screenshot(region=record_area)
        shot = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
        cv2.imwrite(save_abs, shot)

        x, y, ww, hh = record_area
        random_click_mouse((x, y, x + ww, y + hh))

        json_path = f"{QIYUAN_PREFIX}/{fn}".replace("\\", "/")
        entry["rounds"][0].append(json_path)

        print(f"[RECORD] saved: {json_path}")

    print("[RECORD] done.\n")


# =========================
# Main loop: click until question changes
# =========================
def main():
    table = load_table(JSON_PATH)
    qmap = table.get("questions", {})

    ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)

    # your existing window
    x, y, w, h = window_capture_areas_[0]
    focus_region = (x + w // 3, y, w - w // 3, h)

    prev_q = None
    miss_count = 0
    miss_limit = 6      # after N consecutive misses -> record mode (tune)
    tick_sleep = 0.25

    while True:
        # fresh capture + OCR each tick
        pil = pyautogui.screenshot(region=focus_region)
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

        result = ocr.ocr(img, cls=True)
        q = extract_question(result, min_conf=0.55)

        # not in quiz UI
        if not q:
            prev_q = None
            miss_count = 0
            time.sleep(tick_sleep)
            continue

        # question changed
        if prev_q is None or q != prev_q:
            print(f"[Q] {q}")
            prev_q = q
            miss_count = 0

        matched_q = resolve_similar_question_key(q, qmap, min_ratio=0.86)
        if matched_q and matched_q != q:
            print(f"[Q~] OCR '{q}' -> matched '{matched_q}'")

        entry = qmap.get(matched_q) if matched_q else None

        # If not in json -> record immediately
        if entry is None:
            record_mode_add_images(table, q)
            save_table(JSON_PATH, table)
            table = load_table(JSON_PATH)
            qmap = table.get("questions", {})
            miss_count = 0
            time.sleep(0.2)
            continue

        images = get_image_list(entry)

        # Try click any known template
        clicked = try_click_any(images, screen_area=window_capture_areas_[0])

        if clicked:
            miss_count = 0
            time.sleep(0.65)  # let UI respond after click
            continue

        # No match this tick
        miss_count += 1
        if miss_count >= miss_limit:
            print(f"[MISS] no template matched for '{q}' -> record append")
            record_mode_add_images(table, q)
            save_table(JSON_PATH, table)
            table = load_table(JSON_PATH)
            qmap = table.get("questions", {})
            miss_count = 0
            time.sleep(0.2)
            continue

        time.sleep(tick_sleep)


if __name__ == "__main__":
    main()
