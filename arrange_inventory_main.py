import cv2
import numpy as np
import pyautogui
from config import *
from helpers import *
import image_matching as im
from logger import logger
from collections import defaultdict

# # Load the image (both template and screen capture)
# screenshot = pyautogui.screenshot()
# # screenshot = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
# # template = cv2.imread("img_templates/baotu_clicks.png", cv2.IMREAD_UNCHANGED)

# # # Convert the image to HSV color space
# # hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# # # Define the range of yellow color in HSV space
# # lower_yellow = np.array([20, 100, 100])  # Lower bound of yellow
# # upper_yellow = np.array([40, 255, 255])  # Upper bound of yellow

# # # Create a mask to isolate yellow areas
# # yellow_mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)

# # # Apply the mask to the original image
# # yellow_filtered = cv2.bitwise_and(image, image, mask=yellow_mask)

# # image = cv2.imread("screenshot.png", cv2.IMREAD_COLOR)

# # Convert to grayscale
# gray_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

# # Apply adaptive thresholding to isolate text (since background is dark)
# thresholded_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2)

# # Display the filtered yellow areas (for debugging)
# cv2.imshow("template", thresholded_image)
# cv2.moveWindow("template", 100, 100)
# cv2.waitKey(0)
# cv2.destroyAllWindows()




# # click_daily_panel = im.find_icon_each_window(activity_panel_path, screen_area=window_capture_areas_,return_details=True)
# mijing_clicks = []
# # prev_images = []
# for window in window_capture_areas_:
#     logger.info("Fiding Mijing clicking areas")
#     mijing_click, val = im.find_filtered_icons(mijing_click_path, screen_area=window, threshold=0.70,return_details=True)
#     logger.info(f"Found Shimen area at {mijing_click} value: {val}")
#     # random_click_mouse(mijing_click)

#     x,y,x1,y1 = mijing_click
#     click_width = x1 - x
#     click_height = y1 - y
#     current_image = im.capture_region((x, y, click_width, click_height))
#     # prev_images.append(im.capture_region(region=(x, y, x1-x, y1-y)))
#     mijing_clicks.append(mijing_click)

# prev_images = im.capture_regions(mijing_clicks)

# for i, image in enumerate(prev_images):
#     index = f"index {i+1}"
#     cv2.imshow(index, image)

# cv2.waitKey(0)
# cv2.destroyAllWindows()

# click_activity_panel()
# return_home()
# clicks = selection_clicks = click_selection_menu(expected_num=len(window_capture_areas_),
#                                                  previous_task=mijing_path)
# safe_click_each_window(mijing_path,clicks)

# im.find_all_icons(activity_panel_path)



# matches = find_icons_from_screen_per_window(icon_tasks, window_capture_areas_)

# for bbox, tag in matches:
#     if tag in action_map:
#         action_map[tag](bbox)

# matches = im.find_icons_from_each_window("img_templates/items_to_sell/", window_capture_areas_)
# for (a, b, c) in matches:
#     print(f"found at {a} of {b} with confidence {c}")
#     # sell(bbox)

# screenshot = pyautogui.screenshot()
# full_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
# template = cv2.imread("img_templates/items_to_sell/e.png")
# template1 = cv2.imread("img_templates/items_to_sell/d.png")
# # a,b = im.find_matches(template,template1)
# # print(a,b)

# # Run template matching
# result = cv2.matchTemplate(full_image, template, cv2.TM_CCOEFF_NORMED)
# min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

# # Extract matched region
# top_left = max_loc
# h, w = template.shape[:2]
# matched_region = full_image[top_left[1]:top_left[1]+h, top_left[0]:top_left[0]+w]

# # Compute pixel-wise difference
# diff = cv2.absdiff(template, matched_region)
# gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
# _, thresh = cv2.threshold(gray_diff, 25, 255, cv2.THRESH_BINARY)

# # Highlight mismatches in red
# highlighted = matched_region.copy()
# highlighted[thresh > 0] = [0, 0, 255]  # Red where pixels differ

# # Draw rectangle around matched region in original screenshot
# cv2.rectangle(full_image, top_left, (top_left[0]+w, top_left[1]+h), (0, 255, 0), 2)

# # Show outputs
# cv2.imshow("Screenshot with Match", full_image)
# cv2.imshow("Matched Region with Differences", highlighted)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

# # Print similarity score
# print(f"Match confidence: {max_val * 100:.2f}%")



icon_tasks = [
              {"folder": resource_path("img_templates", "inventory_clean", "items_to_sell"), "key": "sell", "threshold": 0.80},
              {"folder": resource_path("img_templates", "inventory_clean", "items_to_discard"), "key": "discard", "threshold": 0.80},
              {"folder": resource_path("img_templates", "inventory_clean", "items_to_stash"), "key": "stash", "threshold": 0.80},
              {"folder": resource_path("img_templates", "inventory_clean", "items_to_medicine"), "key": "medicine", "threshold": 0.80},
             ]

def go_to_market():
    results = im.find_icons_one_per_window(resource_path("img_templates", "market_sell"), window_capture_areas_)
    for result, val, file_name in results:
        logger.info(f"market sell found at {result} with val: {val} name is {file_name}")
        random_click_mouse(result)
    time.sleep(random.uniform(0.5,1.5))
               
    results,vals = im.find_icon_each_window(inventory_additional_options_path)
    for result, val, in zip(results,vals):
        logger.info(f"found additional options at {result} with {val}")
        random_click_mouse(result)
    time.sleep(random.uniform(0.5,1.5))
               
    results,vals = im.find_icon_each_window(market_to_sell_path)
    for result, val, in zip(results,vals):
        logger.info(f"found market to sell at {result} with {val}")
        random_click_mouse(result)
    time.sleep(random.uniform(0.5,1.5))
               
    results,vals = im.find_icon_each_window(market_launch_path)
    for idx, (result, val) in enumerate(zip(results,vals)):
        logger.info(f"found market sell launch at {result} with {val}")
        random_click_mouse(result)
        time.sleep(random.uniform(0.5,1.5))

        result, val = im.find_icon_on_screen(confirm_seven_days_path, screen_area=window_capture_areas_[idx])
        logger.info(f"found confirm seven days at {result} with {val}")
        if result:
            random_click_mouse(result)
            result, val = im.find_icon_on_screen(market_sell_confirm_path, screen_area=window_capture_areas_[idx])
            logger.info(f"found confirm at {result} with {val}")
            random_click_mouse(result)

def market_sell(bbox_list):
    for bbox, val, file_name in bbox_list:
        logger.info(f"market sell found at {bbox} with val: {val} name is {file_name}")
        random_click_mouse(bbox)

        window_id = get_window_area(bbox[0],bbox[1])
        result, val = im.find_icon_on_screen(market_launch_path,screen_area=window_capture_areas_[window_id])
        logger.info(f"found market launch at {result} with {val}")
        random_click_mouse(result)

def sell_items(bbox_list):
    results, val = im.find_icon_each_window(inventory_unselected_path, threshold=0.98)
    logger.info(f"unselected inventories are at {results} with val: {val}") 
    for result in results:
        if result:
            random_click_mouse(result)

    for bbox in bbox_list:
        random_click_mouse(bbox)
        time.sleep(random.uniform(0.5,1.5))

        window_idx = get_window_area(bbox[0], bbox[1])

        result, val = im.find_icon_on_screen(auction_sell_path, screen_area=window_capture_areas_[window_idx], threshold=0.80)
        logger.info(f"found auction_sell at {result} with {val}")
        random_click_mouse(result)
        time.sleep(random.uniform(0.5,1.5))
        
        result,val = im.find_icon_on_screen(sell_path, screen_area=window_capture_areas_[window_idx], threshold=0.90)
        logger.info(f"found sell_path at {result} with {val}")
        random_click_mouse(result)
        time.sleep(random.uniform(0.5,1.5))

        result,val = im.find_icon_on_screen(sell_path,screen_area=window_capture_areas_[window_idx], threshold=0.90)
        logger.info(f"found sell_path at {result} with {val}")
        if result:
            random_click_mouse(result)
            time.sleep(random.uniform(0.5,1.5))

def discard_items(bbox_list):
    results, val = im.find_icon_each_window(inventory_unselected_path, threshold=0.98)
    logger.info(f"unselected inventories are at {results} with val: {val}") 
    for result in results:
        if result:
            random_click_mouse(result)

    for bbox in bbox_list:
        random_click_mouse(bbox)   
        time.sleep(random.uniform(0.5,1.5))

        window_idx = get_window_area(bbox[0], bbox[1])
        result, val = im.find_icon_on_screen(discard_item_path, screen_area=window_capture_areas_[window_idx], threshold=0.90)
        logger.info(f"found discard_item at {result} with {val}")
        random_click_mouse(result)
        time.sleep(random.uniform(0.5,1.5))

        result,val = im.find_icon_on_screen(discard_confirm_path, screen_area=window_capture_areas_[window_idx], threshold=0.80)
        logger.info(f"found discard_confirm_path at {result} with {val}")
        random_click_mouse(result)
        time.sleep(random.uniform(0.5,1.5))

def stash_items(bbox_list):
    results, val = im.find_icon_each_window(stash_unselected_path, threshold=0.98)
    logger.info(f"unselected stashes are at {results} with val: {val}") 
    for result in results:
        if result:
            random_click_mouse(result)

    for bbox in bbox_list:
        random_click_mouse(bbox, double_click=True)

def use_medicine(bbox_list):
    results, val = im.find_icon_each_window(inventory_unselected_path, threshold=0.98)
    logger.info(f"unselected inventories are at {results} with val: {val}") 
    for result in results:
        if result:
            random_click_mouse(result)

    for bbox in bbox_list:
        random_click_mouse(bbox)   
        time.sleep(random.uniform(0.5,1.5))

        window_idx = get_window_area(bbox[0], bbox[1])
        result, val = im.find_icon_on_screen(item_option_more_path, screen_area=window_capture_areas_[window_idx], threshold=0.90)
        logger.info(f"found item_option_more at {result} with {val}")
        random_click_mouse(result)
        time.sleep(random.uniform(0.5,1.5))

        result,val = im.find_icon_on_screen(item_vast_use_path, screen_area=window_capture_areas_[window_idx], threshold=0.80)
        logger.info(f"found item_vast_use_path at {result} with {val}")
        random_click_mouse(result)
        time.sleep(random.uniform(0.5,1.5))

        result,val = im.find_icon_on_screen(item_use_confirm_path, screen_area=window_capture_areas_[window_idx], threshold=0.80)
        logger.info(f"found item_use_confirm_path at {result} with {val}")
        random_click_mouse(result)
        time.sleep(random.uniform(0.5,1.5))

def double_click_items(bbox_list):
    results, val = im.find_icon_each_window(inventory_unselected_path, threshold=0.98)
    logger.info(f"unselected inventories are at {results} with val: {val}")
    for result in results:
        if result:
            random_click_mouse(result)

    for bbox in bbox_list:
        window_idx = get_window_area(bbox[0], bbox[1])
        if window_idx is None:
            logger.warning(f"Cannot find window for double_click item at {bbox}")
            continue

        random_click_mouse(bbox, double_click=True)
        time.sleep(0.3)

        result, val = im.find_icon_on_screen(
            resource_path("img_templates", "ovveride.png"),
            screen_area=window_capture_areas_[window_idx],
            threshold=0.80,
        )
        logger.info(f"found ovveride at {result} with {val}")
        if result:
            random_click_mouse(result)
            time.sleep(0.3)


action_map = {
    "sell": sell_items,
    "discard": discard_items,
    "stash": stash_items,
    "medicine": use_medicine,
}

def process_inventory_with_scrolling(icon_tasks, window_capture_areas, drag_area, action_map, max_scrolls=5):
    # inventory_clicks, vals = im.find_icon_each_window(inventory_path, threshold=0.85)
    # for click,val in zip(inventory_clicks,vals):
    #     logger.info(f"found inventory_clicks at {click} with {val}")
    #     random_click_mouse(click)

    # go_to_market()
    # for i in range(7):
    #     results = im.find_icons_one_per_window("img_templates/in_market", right_half_areas_)
    #     logger.info(f"iteration {i}, market sell {results}")
    #     market_sell(results)
    
    # results, vals = im.find_icon_each_window(market_close_path)
    # for result, val in zip(results,vals):
    #     logger.info(f"found market_close_path at {result} with {val}")
    #     random_click_mouse(result)

    # results, vals = im.find_icon_each_window(inventory_arrange_path)
    # for result, val in zip(results, vals):
    #     logger.info(f"found inventory_arrange_path at {result} with {val}")
    #     random_click_mouse(result)

    reset_inventory_to_top(window_capture_areas_, drag_area)

    # Arrangement passes do not consume the downward-scroll budget.
    arrange_count = 0
    scroll_count = 0

    while True:
        matches = im.find_icons_from_each_window(icon_tasks, window_capture_areas)

        # if not matches:
        #     print(f"No matches found after {scroll_count} scrolls. Ending scan.")
        #     break

        grouped = defaultdict(list)
        for bbox, tag, val, f_name in matches:
            logger.info(f"found tag {tag} at {bbox}, it is a {f_name} with value {val}")
            grouped[tag].append(bbox)

        for tag, bbox_list in grouped.items():
            if tag in action_map:
                action_map[tag](bbox_list)

        # Always scan the position reached by the final permitted scroll.
        if arrange_count >= 2 and scroll_count >= max_scrolls:
            break

        for window in window_capture_areas_:
            if arrange_count < 2:
                result, val = im.find_icon_on_screen(inventory_unselected_path, screen_area=window, threshold=0.98)
                logger.info(f"unselected inventories are at {result} with val: {val}") 
                if result:
                    random_click_mouse(result)

                result, val = im.find_icon_on_screen(inventory_arrange_path,screen_area=window, threshold=0.90)
                if result:
                    logger.info(f"found inventory_arrange_path at {result} with {val}")
                    random_click_mouse(result)
            else:
                drag_inventory(window, direction="down", drag_area=drag_area)
        time.sleep(random.uniform(1.5, 2.5))
        if arrange_count < 2:
            arrange_count += 1
        else:
            scroll_count += 1

    reset_inventory_to_top(window_capture_areas_, drag_area)

    results, vals = im.find_icon_each_window(market_close_path)
    for result, val in zip(results,vals):
        logger.info(f"found market_close_path at {result} with {val}")
        random_click_mouse(result)

    print("Finished inventory scanning.")

def arrange_inventory():
    inventory_clicks, _ = im.find_icon_each_window(inventory_path, threshold=0.85)
    for click in inventory_clicks:
        random_click_mouse(click)

    process_inventory_with_scrolling(icon_tasks, right_half_areas_, inventory_area_, action_map)


if __name__ == "__main__":
    arrange_inventory()

