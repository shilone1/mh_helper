import cv2
import numpy as np
import pyautogui
import time
import random
from image_matching import find_icon_on_screen
from main import click_icon
from mouse_action import random_click_mouse


# # Load the cropped screenshot and the button template
# template_path = "img_templates/bbb.png"

# screenshot = pyautogui.screenshot(None)
# img_templates/skip_cinematic
# sscreenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
# cv2.imshow("a", screenshot)
# cv2.waitKey(0)
# template = cv2.imread(template_path)
# print(template.shape[:2])
# # Perform template matching
# result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
# min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
# print(max_val, max_loc)

# if max_val > 0.8:  # Adjust threshold to account for text variations
#     print(f"Button found at location: {max_loc}")
# else:
#     print("Button not found")




# screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
# template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

# # Detect edges using Canny edge detection
# screenshot_edges = cv2.Canny(screenshot_gray, 50, 150)
# template_edges = cv2.Canny(template_gray, 50, 150)

# # Perform template matching on the edges
# result = cv2.matchTemplate(screenshot_edges, template_edges, cv2.TM_CCOEFF_NORMED)
# min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

# print("canny: ", max_val)
# if max_val > 0.8:  # Adjust threshold based on edge clarity
#     print(f"Button found at location: {max_loc}")
# else:
#     print("Button not found")





# search_region = screenshot

# # Convert the search region to grayscale and apply thresholding to isolate the button
# gray_region = cv2.cvtColor(search_region, cv2.COLOR_BGR2GRAY)
# _, binary_region = cv2.threshold(gray_region, 200, 255, cv2.THRESH_BINARY_INV)

# Detect contours in the binary image
# contours, _ = cv2.findContours(binary_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# print(contours)
# # Find the largest contour, assuming it's the button
# if contours:
#     largest_contour = max(contours, key=cv2.contourArea)
#     x, y, w, h = cv2.boundingRect(largest_contour)
WINDOW_WIDTH = 653  # Width of each game window
WINDOW_HEIGHT = 517  # Height of each game window
WINDOW_FOCUS_WIDTH = 2* WINDOW_WIDTH // 3

in_battle_icon_path = "img_templates/in_battle.png"
skip_cinematic_path = "img_templates/skip_cinematic.png"
go_battle_path = "img_templates/go_battle.png"
selection_menu_path = "img_templates/selection_menu.png"
dungeon_completed_path = "img_templates/dungeon_completed.png"

def find_icon_in_dungeon(template_path):
    return find_icon_on_screen(template_path, screen_area=(WINDOW_FOCUS_WIDTH, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

def wait_until_click(template_path, click_area= None):
    icon_found = None
    while icon_found == None:
        icon_found = find_icon_in_dungeon(template_path)
        time.sleep(random.uniform(3,5))

    if click_area != None:
        icon_found = click_area
    # result = find_icon_on_screen(skip_cinematic_path)
    print(icon_found)
    random_click_mouse(*icon_found)

def dungeon_process():
    wait_until_click(skip_cinematic_path)
    wait_until_click(go_battle_path, click_area=(500, 130, 625, 170))
    wait_until_click(selection_menu_path, click_area= (475, 360, 600, 380))# 125 20      menu at 437 310
    # random_click_mouse(500, 130, 625, 170) # going_to_battle
    # time.sleep(10)
    # random_click_mouse(475, 360, 600, 380) # battle

    while (find_icon_on_screen(in_battle_icon_path) != None):
        print("battle is not finished yet")
        time.sleep(30)

for i in range(3):
    dungeon_process()

wait_until_click(skip_cinematic_path)
wait_until_click(dungeon_completed_path, click_area=(500, 130, 625, 170))
# random_click_mouse(500, 130, 625, 170) # going_to_battle
# time.sleep(10)
# random_click_mouse(475, 360, 600, 380) # battle

# wait_until_click(skip_cinematic_path)
# wait_until_click(go_battle_path, click_area=(500, 130, 625, 170))
# wait_until_click(selection_menu_path, click_area= (475, 360, 600, 380))

# while (find_icon_on_screen(in_battle_icon_path) != None):
#     print("battle is not finished yet")
#     time.sleep(30)

# # icon_found = None
# # while icon_found == None:
# #     icon_found = find_icon_in_dungeon(skip_cinematic_path)
# #     time.sleep(5)

# # random_click_mouse(icon_found)
# # time.sleep(10)
# # random_click_mouse(500, 130, 625, 170) # going_to_battle
# wait_until_click(skip_cinematic_path)
# wait_until_click(go_battle_path, click_area=(500, 130, 625, 170))
# wait_until_click(selection_menu_path, click_area= (475, 360, 600, 380))

# while (find_icon_on_screen(in_battle_icon_path) != None):
#     print("battle is not finished yet")
#     time.sleep(30)