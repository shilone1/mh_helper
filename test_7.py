import cv2
import numpy as np
import pyautogui
from config import *
from helpers import *
import image_matching as im
from logger import logger
from collections import defaultdict
from image_matching import *

answer_areas = [(230,245,390,285), (410,245,565,285), (230,300,390,340), (410,300,565,340)]

for i in range(10):

    for window in window_capture_areas_:
        random_index = random.randint(0,3)
        picked_area = answer_areas[random_index]
        x, y, x1, y1 = picked_area

        topx, topy, _, _ = window
        start_x = topx + x
        start_y = topy + y
        end_x = topx + x1
        end_y = topy + y1
        random_click_mouse((start_x,start_y,end_x,end_y),quick_mode=True)

    result, val = im.find_icon_on_screen(use_item_path)
    if result:
        logger.info(f"Found use_item_path, location {result} found value: {val}")
        random_click_mouse(result)


results, vals = im.find_icon_each_window(recruit_hall_close_path)
for click, val in zip(results, vals):
    logger.info(f"Found recruit_hall_close_path, location {click} found value: {val}")
    random_click_mouse(click)
time.sleep(3)
