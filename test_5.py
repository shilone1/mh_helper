import os
import sys
import contextlib
import warnings
import time
import random
from mouse_action import random_click_mouse, click_mouse, drag_mouse_vertically
import image_matching as im
import cv2
import pyautogui
from config import *
from logger import logger
import re

# from PIL import Image, ImageDraw

# w, h = 222, 60  # new image size
# mask = Image.new("L", (w, h), 255)  # white background
# draw = ImageDraw.Draw(mask)

# # triangle vertices based on your measurement
# triangle = [(0, 0), (43, 0), (0, 37)]
# draw.polygon(triangle, fill=0)

# mask.save("triangle_mask_222x60.png")
# print("✅ Mask saved as triangle_mask_222x60.png")


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, cv2, numpy as np
from paddleocr import PaddleOCR
from difflib import SequenceMatcher

# logging.getLogger("ppocr").setLevel(logging.WARNING)
# logging.getLogger("paddleocr").setLevel(logging.WARNING)

QIYUAN_BASE = "img_templates/qiyuan_templates/"

qiyuan_answer_dict = {"花果山能对1个敌方目标发动一次攻击，并有概率附加" : ['0.png'],
                      "以下谁有可能是骨精灵的师父？" : ['1_1.png','1_2.png'],
                      "哪个妖怪曾假扮天竺公主？" : ['2_1.png'],
                      "须弥海哪个技能增加己方目标速度，同时增加自身法术伤害？" : ['3_1.png'],
                      "普陀山哪个技能可为多个友方单位增加法术伤害和法术防御？" : ['4_1.png'],
                      "找出3只瑶池珍兽" : ['5_1.png', '5_2.png', '5_3.png'],
                      "找出2个封印型三界群雄" : ['6_1.png', '6_2.png'],
                      "花果山哪个技能可变身成召唤灵造型，对本门派技能进行不同效果强化？" : ['7_1.png'],
                      "花果山被复活时获得了分身效果是因为镶嵌了哪颗经脉？" : ['8_1.png'],
                     }

def normalize(s: str) -> str:
    s = s.strip()
    # remove leading "第X题：" style
    s = re.sub(r"^第\d+题[:：]\s*", "", s)
    # remove trailing "（1/2）" style
    s = re.sub(r"（\d+/\d+）$", "", s)
    # remove spaces
    s = re.sub(r"\s+", "", s)
    return s

def similarity(a: str, b: str) -> float:
    a_norm = normalize(a)
    b_norm = normalize(b)
    return SequenceMatcher(None, a_norm, b_norm).ratio()  # 0.0–1.0

def approx_match(expected: str, detected: str, threshold: float = 0.70) -> bool:
    result = similarity(expected, detected)
    # if result >= threshold:
    #     print(result)
    return result >= threshold

def detect_question_key(result, qiyuan_answer_dict) -> str | None:
    if not result or not result[0]:
        return None

    for box, (text, conf) in result[0]:
        print(text)
        for key in qiyuan_answer_dict.keys():
            if approx_match(text, key):
                return key
    return None

def handle_qiyuan_round(result, qiyuan_answer_dict, screen_area) -> tuple[bool, bool]:
    """
    Returns: (clicked_this_round, question_fully_done)
    - clicked_this_round: True if we clicked a template on this screen
    - question_fully_done: True if all templates for this question are done
    """
    key = detect_question_key(result, qiyuan_answer_dict)
    if key is None:
        print("No matching question key on this screen")
        return False, False

    print(f"Matched question: {key}")
    template_list = qiyuan_answer_dict[key]

    used = qiyuan_used.setdefault(key, set())

    # Try only templates that are not yet used
    for template_path in template_list:
        if template_path in used:
            continue  # already clicked in previous rounds

        full_path = os.path.join(QIYUAN_BASE, template_path)
        res, val = im.find_icon_on_screen(full_path,
                                          screen_area=screen_area)
        if res:
            print(f"Found {template_path}, score={val}")
            random_click_mouse(res)
            used.add(template_path)

            # After clicking ONE template, stop this round.
            all_done = (len(used) == len(template_list))
            return True, all_done

    # No remaining template found on this screen
    print("No remaining templates found this round")
    all_done = (len(used) == len(template_list))
    return False, all_done


# question_text -> set of template paths that have already been clicked
qiyuan_used: dict[str, set[str]] = {}


ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
print("OCR loading completed")

# -------- 1. Capture full screen once --------
x, y, w, h = window_capture_areas_[0]

crop_x = x + w // 3
crop_w = w - w // 3

focus_region = (crop_x, y, crop_w, h)
print("focus_region =", focus_region)

# Efficient capture
full_pil = pyautogui.screenshot(region=focus_region)
full_img = cv2.cvtColor(np.array(full_pil), cv2.COLOR_RGB2BGR)

# -------- 2. Crop using window area #1 --------
# x, y, w, h = window_capture_areas_[0]
# cropped = full_img[y:y+h, x:x+w]   # <-- IMPORTANT: [y:y+h, x:x+w]

# -------- 3. OCR on cropped image --------
result = ocr.ocr(full_img, cls=True)

while True:
    clicked, done = handle_qiyuan_round(result,
                                        qiyuan_answer_dict,
                                        screen_area=window_capture_areas_[0])
    
    if done:
        print("This question is fully completed (all required images clicked)")
        break
    if clicked:
        time.sleep(0.7)
    
    if not done and not clicked:
        print("SOMETHING WENT WRONG")
        break

# if not result or not result[0]:
#     print("❌ No text detected")
# else:
#     for box, (text, conf) in result[0]:
#         for answer_key, answer_value in qiyuan_answer_dict.items():
#             # print("ANSWER: ", answer_key)
#             if approx_match(text, answer_key):
#                 print("FOUND A MATCH!!!!!!!!!!!!!!!!")
#                 template_list = qiyuan_answer_dict[answer_key]
#                 for template_path in template_list:
#                     res, val = im.find_icon_on_screen(template_path, screen_area=window_capture_areas_[0])
#                     if res:
#                         print(val)
#                         random_click_mouse(res)
                
#         print(f"win1 → {text} (conf={conf:.3f})")
