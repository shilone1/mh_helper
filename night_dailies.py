import time
import random
from mouse_action import random_click_mouse, click_mouse, drag_mouse_vertically
import image_matching as im
import cv2
import pyautogui
from logger import logger
from config import *
from helpers import *
from paddleocr import PaddleOCR
from difflib import SequenceMatcher
import re

# aaa_              = [{"template_path": selection_menu_path, "filter_range": None},
#                      {"template_path": auto_battle_path, "filter_range": None},
#                     ]

# in_dungeon_paths_ = [{"template_path": skip_cinematic_path, "filter_range": None},
#                      {"template_path": selection_menu_path, "filter_range": None},
#                      {"template_path": go_battle_path, "filter_range": None},
#                      {"template_path": dungeron_click_continue_path, "filter_range": None},
#                      {"template_path": auto_battle_path, "filter_range": None},
#                      {"template_path": dungeon_completed_path, "filter_range": None},
#                     ]

def normalize(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip()
    # Keep ONLY Chinese characters (delete everything else)
    s = re.sub(r'[^\u4e00-\u9fff]', '', s)
    return s

def similarity(a: str, b: str) -> float:
    a_norm = normalize(a)
    b_norm = normalize(b)
    return SequenceMatcher(None, a_norm, b_norm).ratio()

def approx_match(expected: str, detected: str, threshold: float = 0.8) -> bool:
    # Core rule: For "门派闯关", return True if 3/4 characters match
    if expected == "门派闯关":
        expected_chars = list(normalize(expected))  # ['门','派','闯','关']
        detected_chars = list(normalize(detected))
        
        # Count how many expected chars are present in detected text
        match_count = 0
        for char in expected_chars:
            if char in detected_chars:
                match_count += 1
        
        # Return True if 3+ chars match (3/4 rule)
        return match_count >= 2
    
    # Keep original logic for all other text matches
    a_norm = normalize(expected)
    b_norm = normalize(detected)
    return SequenceMatcher(None, a_norm, b_norm).ratio() >= threshold

def night_daily():

    is_dungeon_completed = False
    while not is_dungeon_completed:
        screenshot = pyautogui.screenshot(region=window_capture_areas_[0])
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        result = ocr.ocr(screenshot, cls=True)
    
        for box, (text, conf) in result[0]:
            print(text)
            if text == "召唤灵梦境":
                random_click_mouse((500, 130, 625, 170), double_click=False)
                time.sleep(random.uniform(2,3))
                break
            elif approx_match("门派闯关", text):
                print("found menpai!!")
                random_click_mouse((500, 130, 625, 170), double_click=True)
                time.sleep(random.uniform(2,3))
                break               

        selection_click = click_selection_menu(expected_num=1)
        random_click_mouse(*selection_click)
        time.sleep(random.uniform(5,10))

        while True:
            result, val = im.find_icon_on_screen(auto_battle_path, screen_area=window_capture_areas_[0])
            print("auto battle found with value %d at %d", val, result)
            if result is None:
                time.sleep(random.uniform(1,2))
                break

            print("battle is not done yet")
            time.sleep(random.uniform(3,5))

        print("AAAAAAAAAAAAAAAAAAAAAAAAA")
        time.sleep(random.uniform(1.0,1.5))

def dungeon_process():
    print("AAAAAAAAAA")
    is_dungeon_completed = False
    while not is_dungeon_completed:
        dungeon_results, vals = im.find_multiple_icons_on_screen(in_dungeon_paths_, screen_area=window_capture_areas_[0], threshold=0.78)
        print(f"Dungeon processes {dungeon_results} with {vals}")
        for i, result in enumerate(dungeon_results):
            if result == None:
                continue
            if i == 0:
                print("Skipping dungeon cinematic")
                random_click_mouse(result)
            elif i == 1:
                print("Clicking selection menu")
                random_click_mouse((475, 360, 600, 380))
            elif i == 2:
                print("Clikcing to go to battle")
                random_click_mouse((500, 130, 625, 170))
            elif i == 3:
                print("Clicking to continue")
                random_click_mouse(result)
            elif i == 4:
                print("Battle detected")
                time.sleep(random.uniform(20,30))
                while (im.find_icon_on_screen(in_battle_icon_path)[0] != None):
                    print("battle is not finished yet")
                    time.sleep(random.uniform(5,10))
            elif i == 5:
                print("Dungeon completed")
                random_click_mouse((500, 130, 625, 170))
                is_dungeon_completed = True
            break

        print("End of dungeon process while loop")
        time.sleep(random.uniform(3,5))

if __name__ == "__main__":
    # go_to_quest(menpai_chuangguan_path, mask_path=mask_path_, screen_area=window_capture_areas_[0], threshold=0.80)
    # random_click_mouse((475, 360, 600, 380))
    # print("aaaa")
    # random_click_mouse((475, 360, 600, 380))
    ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
    print("OCR loading completed") 
    #night_daily()
    dungeon_process()
