import os
import cv2
import numpy as np
import pyautogui
from logger import logger
from config import window_capture_areas_
# from mouse_action import random_click_mouse

def capture_region(region):
    """Captures a specific region on the screen."""
    screenshot = pyautogui.screenshot(region=region)
    screenshot.save("aaa.png")
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

def capture_regions(regions):
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    results = []
    for region in regions:
        x,y,x1,y1 = region
        results.append(screenshot[y:y1, x:x1])

    return results
    

def has_region_changed(prev_image, curr_image, threshold=0.90):
    """Compares two images and returns if they are different."""
    result = cv2.matchTemplate(curr_image, prev_image, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    max_val = format_confidence(max_val)

    if max_val > threshold:
        return True, max_val
    else:
        return False, max_val

def format_confidence(value, decimals=2):
    """Formats the confidence score to the specified decimal places."""
    return round(value, decimals)

def find_matches(curr_image, template, mask=None, screen_area=None, threshold=0.80):
    # print('curr_image:', curr_image.shape, curr_image.dtype)
    # print('template:', template.shape, template.dtype)
    match_result = cv2.matchTemplate(curr_image, template, cv2.TM_CCOEFF_NORMED, mask=mask)
    template_height, template_width = template.shape[:2]

    _, max_val, _, max_loc = cv2.minMaxLoc(match_result)
    max_val = format_confidence(max_val)
    # print("found match at :", max_val, " location : ", max_loc)

    if max_val > threshold:
        top_left = (max_loc[0] + (screen_area[0] if screen_area else 0),
                    max_loc[1] + (screen_area[1] if screen_area else 0))
        bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
        bounding_box = (*top_left, *bottom_right)

        return bounding_box, max_val
    else:
        return None, None

def compute_iou(current_box, box):
    x1, y1, x2, y2 = current_box
    x1_, y1_, x2_, y2_ = box

    inter_x1 = max(x1, x1_)
    inter_y1 = max(y1, y1_)
    inter_x2 = min(x2, x2_)
    inter_y2 = min(y2, y2_)

    if inter_x1 < inter_x2 and inter_y1 < inter_y2:
        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        area_box1 = (x2-x1)*(y2-y1)
        area_box2 = (x2_-x1_)*(y2_-y1_)
        return inter_area/(area_box1 + area_box2 - inter_area)
    
    return 0

def non_maximum_suppresion(boxes, scores, iou_threshold=0.5):
    if len(boxes) == 0:
        return []
    
    boxes = np.array(boxes)
    scores = np.array(scores)

    indices= np.argsort(scores)[::-1]
    sorted_boxes = boxes[indices]

    keep = []
    while len(sorted_boxes) > 0:
        current_box = sorted_boxes[0]
        keep.append(current_box)
        remaining_boxes = sorted_boxes[1:]

        sorted_boxes = [box for box in remaining_boxes if compute_iou(current_box, box) < iou_threshold]

    return keep


def find_icon_on_screen(template_path, mask_path=None, screen_area=None, threshold=0.8):
    screenshot = pyautogui.screenshot(region=screen_area)
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE) if mask_path else None

    return find_matches(screenshot, template, mask=mask, screen_area=screen_area, threshold=threshold)

def find_all_icons(template_path, 
                   mask_path=None, 
                   screen_area=None, 
                   threshold=0.8,
                   use_nms=False):
    
    # Take a screenshot of the screen
    screenshot = pyautogui.screenshot(region=screen_area)
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    template_height, template_width = template.shape[:2]
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE) if mask_path else None

    # Match the template on the screenshot
    match_result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED, mask=mask)

    # Get locations of matches above the threshold
    locations = np.where(match_result >= threshold)
    match_values = match_result[locations]
    # print(match_values)

    # Extract all matched positions
    matches = list(zip(*locations[::-1]))  # Reverse x, y to align with (left, top) format

    for loc, val in zip(matches, match_values):
        logger.info(f"found {loc} with val: {val}")

    match_boxes = []

    for (x, y) in matches:
        topleft_x = x
        topleft_y = y
        bottomright_x = x + template_width  
        bottomright_y = y + template_height
        # print(topleft_x,topleft_y,bottomright_x,bottomright_y)  
        
        match_boxes.append((topleft_x, topleft_y, bottomright_x, bottomright_y))

    if use_nms:
        filtered_boxes = non_maximum_suppresion(match_boxes, match_values.tolist())
        return filtered_boxes
    else:
        return match_boxes

def find_icons_by_regions(template_path, mask_path=None, screen_area=None, threshold=0.80):
    all_matches = []
    for area in screen_area:
        matches = find_all_icons(template_path, mask_path, screen_area=area, threshold=threshold,use_nms=True)
        all_matches.extend(matches)

    return all_matches

# to avoid overlapping match with small templates
def find_small_icons_by_window(template_path, mask_path=None, screen_area=None, threshold=0.80):
    all_matches = []
    for area in screen_area:
        match = find_icon_on_screen(template_path, mask_path, screen_area=area,)       
        if match:
            all_matches.append(match)
    
    return all_matches 

def find_multiple_icons_on_screen(templates_info, mask_path=None, screen_area=None, threshold=0.80, image=None):    
    if image is None:
        # Take screenshot normally
        screenshot = pyautogui.screenshot(region=screen_area)
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    else:
        # Use provided image
        screenshot = image.copy()

        # If screen_area is given → crop the provided image
        if screen_area is not None:
            x, y, w, h = screen_area
            screenshot = screenshot[y:y+h, x:x+w]

    matches = []
    vals = []

    for info in templates_info:
        template_path, filter_range = info.values()

        # Load the template
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE) if mask_path else None

        # Apply color filtering if specified
        if filter_range:
            hsv_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            lower_bound, upper_bound = filter_range
            color_mask = cv2.inRange(hsv_screenshot, lower_bound, upper_bound)
            filtered_screenshot = cv2.bitwise_and(screenshot, screenshot, mask=color_mask)

            match_data, val = find_matches(filtered_screenshot, template, mask=mask, screen_area=screen_area, threshold=threshold)
        else:
            match_data, val = find_matches(screenshot, template, mask=mask, screen_area=screen_area, threshold=threshold)

        matches.append(match_data)
        vals.append(val)

    return matches, vals


def find_filtered_icons(template_path, screen_area=None, threshold=0.80):
    screenshot = pyautogui.screenshot(region=screen_area)
    image = np.array(screenshot)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_yellow = np.array([20, 90, 140])
    upper_yellow = np.array([40, 255, 255])

    yellow_mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    yellow_filtered = cv2.bitwise_and(image, image, mask=yellow_mask)

    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    return find_matches(yellow_filtered, template, screen_area=screen_area, threshold=threshold)

def _apply_hsv_filter_bgr(bgr_img,
                          lower_hsv=np.array([20, 90, 140]),
                          upper_hsv=np.array([40, 255, 255])):
    hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
    filtered = cv2.bitwise_and(bgr_img, bgr_img, mask=mask)
    return filtered

def find_icon_each_window(template_path,
                          mask_path=None,
                          screen_area=window_capture_areas_,
                          threshold=0.8,
                          filtering=False,
                          lower_hsv=np.array([20, 90, 140]),
                          upper_hsv=np.array([40, 255, 255])):
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template not found or unreadable: {template_path}")

    mask = None
    if mask_path:
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if mask is None:
            raise FileNotFoundError(f"Mask not found or unreadable: {mask_path}")

    results = []
    vals = []

    for window in screen_area:
        x1, y1, width, height = window
        x2 = x1 + width
        y2 = y1 + height

        window_image = screenshot[y1:y2, x1:x2]

        if filtering:
            window_image = _apply_hsv_filter_bgr(
                window_image,
                lower_hsv=lower_hsv,
                upper_hsv=upper_hsv
            )

        match_result = find_matches(
            window_image,
            template,
            mask=mask,
            screen_area=window,
            threshold=threshold
        )

        # assuming find_matches returns (best_bbox_or_point, best_val) or similar
        results.append(match_result[0])
        vals.append(match_result[1])

    return results, vals

def boxes_overlap(box1, box2):
    x1, y1, x2, y2 = box1
    x1_, y1_, x2_, y2_ = box2
    return not (x2 <= x1_ or x2_ <= x1 or y2 <= y1_ or y2_ <= y1)

def find_icons_from_each_window(task_list, windows):
    screenshot = pyautogui.screenshot()
    full_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    final_results = []

    for task in task_list:
        folder = task["folder"]
        tag = task["key"]
        threshold = task.get("threshold", 0.8)

        template_files = [f for f in os.listdir(folder) if f.endswith(".png")]
        templates = [(cv2.imread(os.path.join(folder, f), cv2.IMREAD_COLOR), f) for f in template_files]

        for (left, top, width, height) in windows:
            cropped = full_image[top:top + height, left:left + width]

            locked_zones = []
            for template, f_name in templates:
                if template is None:
                    continue

                result = cv2.matchTemplate(cropped, template, cv2.TM_CCOEFF_NORMED)
                h, w = template.shape[:2]
                loc = np.where(result >= threshold)

                for pt in zip(*loc[::-1]):
                    global_box = (left + pt[0], top + pt[1], left + pt[0] + w, top + pt[1] + h)
                    score = result[pt[1], pt[0]]

                    if not any(boxes_overlap(global_box, locked) for locked in locked_zones):
                        final_results.append((global_box, tag, score, f_name))
                        locked_zones.append(global_box)

    return final_results

def find_icons_one_per_window(template_folder, windows, threshold=0.8):

    screenshot = pyautogui.screenshot()
    full_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    template_files = [f for f in os.listdir(template_folder) if f.endswith(".png")]
    templates = [(cv2.imread(os.path.join(template_folder, f), cv2.IMREAD_COLOR), f) for f in template_files]

    matches = []

    for (left, top, width, height) in windows:
        cropped = full_image[top:top + height, left:left + width]

        for template, filename in templates:
            if template is None:
                continue

            result, val = find_matches(cropped, template, screen_area=(left, top), threshold=threshold)
            if result:
                matches.append((result, val, filename))
                break  # Stop after the first match in this window

    return matches

# tasks = [
#     {"template_path": "img_templates/shimen_clicking_area.png", "filter_range":(np.array([20, 90, 100]), np.array([40, 255, 255]))},
#     {"template_path": "img_templates/auto_battle.png", "filter_range": None}, 
#     {"template_path": "img_templates/baotu_clicks.png", "filter_range": None},
# ]

# find_multiple_icons_on_screen(tasks)