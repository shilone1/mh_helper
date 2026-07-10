import time
import random
from mouse_action import random_click_mouse, click_mouse, drag_mouse_vertically
import image_matching as im
import cv2
import pyautogui
from config import *
from logger import logger

def safe_click_each_window(template_path, click_areas, retries=3, delay=(1, 1.5), threshold=0.85):
    status_per_window = [False] * len(click_areas)
    template_img = cv2.imread(template_path, cv2.IMREAD_COLOR)

    for attempt in range(retries):
        for idx, area in enumerate(click_areas):
            if status_per_window[idx] or area is None:
                continue

            logger.info(f"[Window {idx}] Attempt {attempt+1}: clicking area {area}")
            random_click_mouse(area)

        time.sleep(random.uniform(*delay))

        # Take a single screenshot
        full_screen = pyautogui.screenshot()
        full_screen = cv2.cvtColor(np.array(full_screen), cv2.COLOR_RGB2BGR)

        for idx, area in enumerate(click_areas):
            if status_per_window[idx] or area is None:
                continue

            x, y, x1, y1 = area
            w = x1 - x
            h = y1 - y

            cropped = full_screen[y:y+h, x:x+w]
            stuck_result, val = im.has_region_changed(template_img, cropped, threshold=threshold)
            if stuck_result:
                logger.warning(f"[Window {idx}] val: {val} No change detected.")
            else:
                logger.info(f"[Window {idx}] val: {val} State changed — click accepted.")
                status_per_window[idx] = True

        if all(status_per_window):
            logger.info("All windows confirmed click success.")
            break

    return status_per_window

def click_activity_panel():
    to_completes,_ = im.find_icon_each_window(activity_panel_path)

    safe_click_each_window(activity_panel_path, to_completes)

# def find_all_relative_pos(left, top, right, bottom):
#     areas = []
#     for (x, y) in window_positions.values():
#         # Calculate the global position
#         global_left   = left + x
#         global_top    = top + y
#         global_right  = right + x
#         global_bottom = bottom + y

#         print(f"areas found: ({left}, {top}, {right}, {bottom})")

#         # Perform the random click within the area
#         areas.append((global_left, global_top, global_right, global_bottom))
    
#     return areas

def get_window_area(x, y):

    for idx, (left, top, width, height) in enumerate(window_capture_areas_):
        if left <= x <= left + width and top <= y <= top + height:
            return idx  # Return the index or name of the clicked window (e.g., window 1, window 2, etc.)
    return None  # Return None if no window was clicked

def calculate_selection_menu_displace(x,y):
    topleft_x = x + selection_menu_displace_[0]
    topleft_y = y + selection_menu_displace_[1]
    bottomright_x = topleft_x + selection_menu_button_[0]
    bottomright_y = topleft_y + selection_menu_button_[1]
    
    return (topleft_x,topleft_y,bottomright_x,bottomright_y)

# def click_selection_menu(expected_num=1):
#     all_found = False
#     results = []
#     while not all_found:
#         to_completes = im.find_all_icons(selection_menu_path)

#         if len(to_completes) < expected_num:
#             time.sleep(random.uniform(0.5,1.0))
#             continue

#         logger.info(f"selection menu all found at {to_completes}")
#         for i in to_completes:
#             tx, ty, _, _ = i
#             pos = calculate_selection_menu_displace(tx,ty)
#             results.append(pos)

#         all_found = True
#         # random_click_mouse((topleft_x,topleft_y,bottomright_x,bottomright_y))

#     return results

# def click_secondary_panel():
#     #checks the secondary completion (jiuzhuan)
#     is_window_finished = [False] * 5

#     shimen_completes_2,_ = im.find_small_icons_by_window(shimen_completed_2_path, screen_area=window_capture_areas_, threshold=0.85)
#     for shimen_complete_2 in shimen_completes_2:
#         left, top, right, bottom = shimen_complete_2
#         random_click_mouse(shimen_complete_2)
#         clicked_window_index = get_window_area(left, top)
#         is_window_finished[clicked_window_index] = True

#     return is_window_finished

def click_reward_items():
    for window in window_capture_areas_:
        all_item_clicked = False
        memorize_click_pos = None
        while not all_item_clicked:
            click,_ = im.find_icon_on_screen(use_item_path, screen_area=window, threshold=0.80)
            if click == None:
                all_item_clicked = True
                continue
            
            if not memorize_click_pos:
                random_click_mouse(click)
                memorize_click_pos = True
            else:
                click_mouse()
            time.sleep(random.uniform(0.8,1.5))


def go_to_quest(template_path, mask_path=None, screen_area=window_capture_areas_, threshold=0.95):
    print(screen_area)
    clicks_activity_panel, vals = im.find_icon_each_window(activity_panel_path, 
                                                           screen_area=screen_area, 
                                                           threshold=threshold)
    
    for click, val in zip(clicks_activity_panel, vals):
        logger.info(f"Found activity panels, location {click} found value: {val}")
        random_click_mouse(click)
    time.sleep(3)

    #If other timed daily is in the way
    clicks_daily_panel, vals = im.find_icon_each_window(select_daily_panel_path, 
                                                        screen_area=screen_area, 
                                                        threshold=threshold)
    for click, val in zip(clicks_daily_panel, vals):
        logger.info(f"Not in daily panel, location {click} found value: {val}")
        random_click_mouse(click)

    to_completes, vals = im.find_icon_each_window(template_path,
                                                  mask_path=mask_path,
                                                  screen_area=screen_area, 
                                                  threshold=threshold)
                                            
    # logger.info(f"activities templates found at: {to_completes}")

    for click, val in zip(to_completes,vals):
        top_left_x, top_left_y, _, _ = click
        button_left   =  top_left_x + button_relative_area_[0]
        button_top    =  top_left_y + button_relative_area_[1]
        button_right  =  top_left_x + button_relative_area_[2]
        button_bottom =  top_left_y + button_relative_area_[3]

        logger.info(f"Found Target activity, location {click} found value: {val}")
        # Perform the click specifically on the button
        random_click_mouse((button_left, button_top, button_right, button_bottom))


def click_selection_menu(expected_num=1, previous_task=None, max_attempts=5, auto_recovery=False):
    if auto_recovery and previous_task is None:
        raise ValueError("previous_task must be provided when auto_recovery is enabled")
    
    results = [None] * len(window_capture_areas_)
    attempt = 0

    while True:
        matches,_ = im.find_icon_each_window(selection_menu_path, screen_area=window_capture_areas_)
        results = matches
        found_count = sum(1 for m in matches if m is not None)
        # print(found_count)
        logger.info(f"Expecting {expected_num} windows, Found {matches}")

        if found_count >= expected_num:
            break

        attempt += 1

        if auto_recovery and attempt >= max_attempts:
            stuck_indices = [i for i, r in enumerate(results) if r is None]

            if expected_num == 1 and found_count == 0:
                print("[INFO] Leader likely stuck. Retrying go_to_quest on window 0.")
                go_to_quest(previous_task, screen_area=[window_capture_areas_[0]])
            else:
                stuck_areas = [window_capture_areas_[i] for i in stuck_indices]
                print(f"[INFO] Retrying go_to_quest on stuck windows: {stuck_indices}")
                go_to_quest(previous_task, screen_area=stuck_areas)

            attempt = 0
            time.sleep(random.uniform(1.0, 1.5))
            continue

        time.sleep(random.uniform(0.5, 1.0))

    return [calculate_selection_menu_displace(element[0], element[1]) for element in results if element is not None]


def get_inventory_drag_points(window, drag_area=inventory_area_):
    x, y1, x1, y = drag_area
    topx, topy, _, _ = window
    start_x = topx + x
    end_x = topx + x1
    bottom_y = topy + y
    top_y = topy + y1

    lower_y = random.uniform(bottom_y - 20, (bottom_y - top_y) / 2 + top_y)
    upper_y = random.uniform(top_y + 20, (bottom_y - top_y) / 2 + top_y)
    return start_x, end_x, lower_y, upper_y


def drag_inventory(window, direction="up", drag_area=inventory_area_):
    start_x, end_x, lower_y, upper_y = get_inventory_drag_points(window, drag_area)

    if direction == "up":
        area = (start_x, upper_y, end_x, lower_y)
    elif direction == "down":
        area = (start_x, lower_y, end_x, upper_y)
    else:
        raise ValueError(f"Unknown inventory drag direction: {direction}")

    logger.info(f"Dragging inventory {direction} from {area[1]:.1f} to {area[3]:.1f}")
    drag_mouse_vertically(area)


def choose_baotu_in_inventory():
    inventory_clicks,_ = im.find_icon_each_window(inventory_path, threshold=0.85)
    for click in inventory_clicks:
        random_click_mouse(click)
    
    search_phases = (
        ("up", random.randint(4, 6)),
        ("down", random.randint(4, 6)),
    )

    for window in window_capture_areas_:
        logger.info(f"working on window {window}")
        baotu_found = False

        for direction, max_drags in search_phases:
            if baotu_found:
                break

            for attempt in range(max_drags):
                result,_ = im.find_icon_on_screen(baotu_item_path, screen_area=window, threshold=0.85)

                if result != None:
                    random_click_mouse(result, double_click=True)
                    baotu_found = True
                    break

                logger.info(f"Baotu search drag {attempt + 1}/{max_drags} direction={direction}")
                drag_inventory(window, direction=direction)
                time.sleep(random.uniform(0.5,1.5))

        if not baotu_found:
            logger.info("baotu not found or some bugs appeared")


def dig_baotu():
    baotu_task_icons = [{"template_path": use_item_path, "filter_range": None},
                        {"template_path": auto_battle_path, "filter_range": None},
                       ]

    # Initial window status
    window_status = {i: {"state": "waiting", "counter": 0} for i in range(5)}  # Complete, Battle, Waiting

    # Define maximum retries for windows
    MAX_RETRIES = 3

    while any(window["counter"] < MAX_RETRIES for window in window_status.values()):
        for i in window_status:
            # Get the screen region for the current window
            results, _ = im.find_multiple_icons_on_screen(baotu_task_icons, screen_area=window_capture_areas_[i], threshold=0.88)
            
            
            # Process if `use_item` icon is found
            if results[0]:
                random_click_mouse(results[0])  # Click the `use_item` icon
                window_status[i]["counter"] = 0  # Reset counter when action is taken

            # Process if `auto_battle` icon is found
            elif results[1]:
                window_status[i]["state"] = "in_battle"  # Mark as in battle
                window_status[i]["counter"] = 0  # Reset counter in battle state

            # If no icons found, increment the counter if the window is not in a valid state
            elif all(result == None for result in results):
                window_status[i]["counter"] += 1

            # If the window has been checked multiple times without progress, mark as completed
            if window_status[i]["counter"] >= MAX_RETRIES:
                window_status[i]["state"] = "completed"
                logger.info(f"Window {i} task is completed.")
            
            time.sleep(random.uniform(0.4,0.7))
        # Sleep after each check to simulate delay
        time.sleep(random.uniform(7, 14))  # Adjust the sleep time to simulate human behavior

        logger.info("Checking windows progress...")  # Optional log message


#-----------------------------------------Dungeon Related------------------------------------------------------------
def find_icon_in_dungeon(template_path):
    return im.find_icon_on_screen(template_path, screen_area=(WINDOW_FOCUS_WIDTH, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

def wait_until_click(template_path, click_area= None):
    icon_found = None
    exhausted_counter = 0
    while icon_found == None:
        icon_found,_ = find_icon_in_dungeon(template_path)

        exhausted_counter += 1
        if exhausted_counter >= 20:
            return

        time.sleep(random.uniform(1,2))

    if click_area != None:
        icon_found = click_area
    # result = find_icon_on_screen(skip_cinematic_path)
    logger.info(icon_found)
    random_click_mouse(icon_found)
    time.sleep(random.uniform(3,5))

in_dungeon_paths_ = [{"template_path": skip_cinematic_path, "filter_range": None},
                     {"template_path": selection_menu_path, "filter_range": None},
                     {"template_path": go_battle_path, "filter_range": None},
                     {"template_path": dungeron_click_continue_path, "filter_range": None},
                     {"template_path": auto_battle_path, "filter_range": None},
                     {"template_path": dungeon_completed_path, "filter_range": None},
                    ]

def dungeon_process():
    is_dungeon_completed = False
    while not is_dungeon_completed:
        dungeon_results, vals = im.find_multiple_icons_on_screen(in_dungeon_paths_, screen_area=window_capture_areas_[0], threshold=0.78)
        logger.info(f"Dungeon processes {dungeon_results} with {vals}")
        for i, result in enumerate(dungeon_results):
            if result == None:
                continue
            if i == 0:
                logger.info("Skipping dungeon cinematic")
                random_click_mouse(result)
            elif i == 1:
                logger.info("Clicking selection menu")
                random_click_mouse((475, 360, 600, 380))
            elif i == 2:
                logger.info("Clikcing to go to battle")
                random_click_mouse((500, 130, 625, 170))
            elif i == 3:
                logger.info("Clicking to continue")
                random_click_mouse(result)
            elif i == 4:
                logger.info("Battle detected")
                time.sleep(random.uniform(20,30))
                while (im.find_icon_on_screen(in_battle_icon_path)[0] != None):
                    print("battle is not finished yet")
                    time.sleep(random.uniform(5,10))
            elif i == 5:
                logger.info("Dungeon completed")
                random_click_mouse((500, 130, 625, 170))
                is_dungeon_completed = True
            break

        logger.info("End of dungeon process while loop")
        time.sleep(random.uniform(3,5))



    # wait_until_click(skip_cinematic_path)
    # wait_until_click(go_battle_path, click_area=(500, 130, 625, 170))
    # wait_until_click(selection_menu_path, click_area= (475, 360, 600, 380))# 125 20      menu at 437 310

    # while (im.find_icon_on_screen(in_battle_icon_path) != None):
    #     print("battle is not finished yet")
    #     time.sleep(30)

# def do_dungeon():
#     # for i in range(3):
#     #     dungeon_process()

#     # wait_until_click(skip_cinematic_path)
#     # wait_until_click(dungeon_completed_path, click_area=(500, 130, 625, 170))
#     dungeon_process()

def perform_dungeons(elite=False, count=None):
    dungeon_counter = 0
    elite_dungeon_counter = 0
    target_count = NORMAL_DUNGEON_NUM if count is None else int(count)

    if target_count <= 0:
        logger.info("Dungeon count is 0, skipping dungeon task.")
        return

    while True:
        activity_click,_ = im.find_icon_on_screen(activity_panel_path, screen_area=window_capture_areas_[0])
        random_click_mouse(activity_click)

        #If other timed daily is in the way
        click_daily_panel, val = im.find_icon_on_screen(select_daily_panel_path, 
                                                        screen_area=window_capture_areas_[0],
                                                        threshold=0.95)
        if click_daily_panel:
            logger.info(f"Currently not on daily panel {click_daily_panel}, {val}, clicking daily panel")
            random_click_mouse(click_daily_panel)

        time.sleep(random.uniform(2,3))
        dungeon_pos, vals = im.find_multiple_icons_on_screen(dungeon_paths_,
                                                             mask_path=mask_path_,
                                                             screen_area=window_capture_areas_[0], 
                                                             threshold=0.80)
        logger.info(f"dungeons located at: {dungeon_pos} with {vals}")

        # all_none = True

        for i, pos in enumerate(dungeon_pos):
            if pos == None:
                logger.info(f"dungeon {i} not found!!!")
                continue

            logger.info(f"Dungeon found at {pos} with {vals[i]}")
            top_left_x, top_left_y, _, _ = pos
            # all_none = False
            break

        # if all_none:
        #     break

        button_left = top_left_x + button_relative_area_[0]
        button_top = top_left_y + button_relative_area_[1]
        button_right = top_left_x + button_relative_area_[2]
        button_bottom = top_left_y + button_relative_area_[3]

        # Perform the click specifically on the button
        random_click_mouse((button_left, button_top, button_right, button_bottom))
        time.sleep(random.uniform(2,4))

        selection_click = click_selection_menu()
        random_click_mouse(*selection_click)
        # time.sleep(3)

        if elite:
            elite_dungeon_panel,_ = im.find_icon_on_screen(elite_dungeon_panel_path, screen_area=window_capture_areas_[0])
            print(elite_dungeon_panel)
            random_click_mouse(elite_dungeon_panel)
            time.sleep(random.uniform(0.1,0.3))

            dungeon_enter_clicks = im.find_all_icons(dungeon_enter_path, screen_area=window_capture_areas_[0],threshold=0.85)
            random_click_mouse(dungeon_enter_clicks[elite_dungeon_counter])
            time.sleep(random.uniform(1.0, 2.0))

            for window in window_capture_areas_[1:]:
                elite_dungeon_ready,_ = im.find_icon_on_screen(elite_dungeon_ready_path, screen_area=window)
                random_click_mouse(elite_dungeon_ready)
                time.sleep(random.uniform(0.1,0.3))

            elite_dungeon_counter += 1
            time.sleep(random.uniform(5,10))
            dungeon_process()
            if elite_dungeon_counter >= target_count:
                break
            continue

        dungeon_enter_clicks = im.find_all_icons(dungeon_enter_path, screen_area=window_capture_areas_[0],threshold=0.85)
        random_click_mouse(dungeon_enter_clicks[dungeon_counter])
        dungeon_counter += 1
        time.sleep(random.uniform(5,10))
        dungeon_process()

        if dungeon_counter >= target_count:
            break

def perform_zhuagui(rounds=5):
    double_exp_tab_clicks, vals = im.find_icon_each_window(double_exp_tab_path,screen_area=window_capture_areas_)
    for click, val in zip(double_exp_tab_clicks, vals):
        logger.info(f"Found activity panels, location {click} found value: {val}")
        random_click_mouse(click)

    double_exp_acquire_clicks, vals = im.find_icon_each_window(double_exp_acquire_path, screen_area=window_capture_areas_)
    for click, val in zip(double_exp_acquire_clicks, vals):
        logger.info(f"Found double_exp_acquire_path, location {click} found value: {val}")
        random_click_mouse(click, double_click=True)

    party_panel_close_clicks, vals = im.find_icon_each_window(party_panel_close_path, screen_area=window_capture_areas_)
    for click, val in zip(party_panel_close_clicks, vals):
        logger.info(f"Found double_exp_acquire_path, location {click} found value: {val}")
        random_click_mouse(click)

    activity_click,_ = im.find_icon_on_screen(activity_panel_path, screen_area=window_capture_areas_[0])
    random_click_mouse(activity_click)

    logger.info("Performing zhuagui.........")
    zhuagui_click,_ = im.find_icon_on_screen(zhuagui_path, mask_path=mask_path_, screen_area=window_capture_areas_[0], threshold=0.9)
    top_left_x, top_left_y, _, _ = zhuagui_click

    button_left = top_left_x + button_relative_area_[0]
    button_top = top_left_y + button_relative_area_[1]
    button_right = top_left_x + button_relative_area_[2]
    button_bottom = top_left_y + button_relative_area_[3]

    # Perform the click specifically on the button
    random_click_mouse((button_left, button_top, button_right, button_bottom))

    zhuagui_counter = 0
    time.sleep(random.uniform(10,15))
    while zhuagui_counter < rounds:
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
                zhuagui_counter += 1
                is_cycle_done = True
                if zhuagui_counter >= rounds:
                    time.sleep(random.uniform(350,400))
                    break
                random_click_mouse(complete_click)

        time.sleep(random.uniform(5,8))

def return_home():
    expand_bottom_clicks, vals = im.find_icon_each_window(expand_bottom_path) 
    
    for click, val in zip(expand_bottom_clicks, vals):
        if click is None:
            continue

        logger.info(f"Expand bottom found at {click} with {val}")
        random_click_mouse(click)
    
    home_icon_clicks,_ = im.find_icon_each_window(home_icon_path)

    safe_click_each_window(home_icon_path, home_icon_clicks)
