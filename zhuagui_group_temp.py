import time
import random
from mouse_action import random_click_mouse, click_mouse, drag_mouse_vertically
import image_matching as im
import cv2
import pyautogui
from config import *
from helpers import * 
from logger import logger

zhuagui_rounds = 10
windows = [window_capture_areas_[1], window_capture_areas_[2], window_capture_areas_[3]]
zhuagui_counters = [0] * len(windows)
print(windows)
while any(counter < zhuagui_rounds for counter in zhuagui_counters):
    logger.info("New round of zhuagui begins..........")
    selection_menu_clicks = click_selection_menu(expected_num=0)
    print(selection_menu_clicks)
    for click in selection_menu_clicks:
        random_click_mouse(click)
        time.sleep(random.uniform(3,5))
    
    if selection_menu_clicks:
        zhuagui_proceed_clicks, val = im.find_icon_each_window(zhuagui_proceed_path, screen_area=windows, filtering=True)
        for proceed_click in zhuagui_proceed_clicks:
            if proceed_click:
                logger.info(f"zhuagui_proceed at {proceed_click} with val: {val}") 
                random_click_mouse(proceed_click, double_click=True)   
                    # random_click_mouse((500, 185, 626, 231),double_click=True)

    time.sleep(random.uniform(30,50))    
    complete_clicks,_ = im.find_icon_each_window(zhuagui_continue_path, screen_area=windows)
    logger.info(f"Finding zhuagui continue button. {complete_clicks}")

    for idx, complete_click in enumerate(complete_clicks):
        if complete_click is None:
            continue

        zhuagui_counters[idx] += 1
        if zhuagui_counters[idx] >= zhuagui_rounds:
            continue  # stop counting/clicking finished windows
        logger.info(f"[win {idx}] continue FOUND at {complete_click}")
        random_click_mouse(complete_click)

    time.sleep(random.uniform(5,8))