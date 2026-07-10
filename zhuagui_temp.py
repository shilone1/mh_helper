import time
import random
from mouse_action import random_click_mouse, click_mouse, drag_mouse_vertically
import image_matching as im
import cv2
import pyautogui
from config import *
from helpers import *
from logger import logger

zhuagui_counter = 0
while zhuagui_counter < 25:
    logger.info("New round of zhuagui begins..........")
    selection_menu_click = click_selection_menu()
    random_click_mouse(*selection_menu_click)
    time.sleep(3)
    zhuagui_proceed_click, val = im.find_filtered_icons(zhuagui_proceed_path, screen_area=window_capture_areas_[0])
    logger.info(f"zhuagui_proceed at {zhuagui_proceed_click} with val: {val}")
    random_click_mouse(zhuagui_proceed_click, double_click=True)  
    # random_click_mouse((500, 185, 626, 231),double_click=True)

    is_cycle_done = False
    while not is_cycle_done:
        time.sleep(random.uniform(30,50))    
        complete_click,_ = im.find_icon_on_screen(zhuagui_continue_path, screen_area=window_capture_areas_[0])
        logger.info("Finding zhuagui continue button. Next iteration...!")

        if complete_click != None:
            logger.info("zhuagui continue button FOUND!.")
            random_click_mouse(complete_click)
            zhuagui_counter += 1
            is_cycle_done = True

    time.sleep(random.uniform(5,8))