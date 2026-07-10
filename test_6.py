import cv2
import numpy as np
import pyautogui
from config import *
from helpers import *
import image_matching as im
from logger import logger
from collections import defaultdict
from image_matching import *

print(cv2.__version__)
screenshot = pyautogui.screenshot()
# Convert the screenshot to an OpenCV-compatible format
image = np.array(screenshot)
# Convert RGB to BGR (OpenCV uses BGR by default)
image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

# cv2.imwrite("aaaaaaaaaaaaaaaaaaaaa.png", image)
screen_area = window_capture_areas_[0]
screenshot = pyautogui.screenshot(region=screen_area)
screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

# template = cv2.imread("image_templates/fabao_1.png", cv2.IMREAD_COLOR)
path = "img_templates/fabao_1.png"
match_data = im.find_icon_on_screen(path,screen_area=screen_area)
random_click_mouse(match_data[0])

print(match_data)

# cv2.imshow("a", template)
# cv2.waitKey(0)

# dungeon_pos, vals = im.find_multiple_icons_on_screen(dungeon_paths_,
#                                                         mask_path=mask_path_,
#                                                         screen_area=window_capture_areas_[0], 
#                                                         threshold=0.75)
# logger.info(f"dungeons located at: {dungeon_pos} with {vals}")