
import time
import random
import pygetwindow as gw
import numpy as np
from get_windows import enum_windows_by_title, get_window_positions, move_windows_to_positions
from mouse_action import random_click_mouse, click_mouse, drag_mouse_vertically
import image_matching as im
from config import *
from helpers import *
#184 39 205 63


#deprecated
# def click_until_end(template_path, clicking_delay=(3,5), threshold=0.9):
#     exhausted_counter = 0
#     while exhausted_counter < 5:
#         is_in_battles = im.find_all_icons(auto_battle_path)
#         if len(is_in_battles) == 5:
#             print("all 5 windows are in battle, skip checking")
#             time.sleep(random.uniform(5,10))
#             continue

#         matches = im.find_all_icons(template_path,threshold=threshold)
#         if not matches:
#             exhausted_counter += 1
#             continue
            
#         for match in matches:
#             random_click_mouse(match)
        
#         time.sleep(random.uniform(*clicking_delay))


shimen_complete_checks = [{"template_path": shimen_completed_click_path, "filter_range": None},
                          {"template_path": shimen_completed_2_path, "filter_range": None}]

def perform_shimen():
    shimen_clicks = []
    for window in window_capture_areas_:
        shimen_click = im.find_filtered_icons(shimen_clicking_area_path,screen_area=window)
        random_click_mouse(shimen_click)
        shimen_clicks.append(shimen_click)
    
    time.sleep(random.uniform(1,3))
    to_completes = im.find_all_icons(shimen_accept_path, threshold=0.90)
    for i in to_completes:
        random_click_mouse(i)

    #####demo for experiments########################
    # shimen_clicks = [
    # (500, 185, 626, 231),
    # (1142, 185, 1268, 231),
    # (1784, 185, 1910, 231),
    # (1136, 698, 1262, 744),
    # (1778, 698, 1904, 744)
    # ]

    is_window_finished = [False] * len(shimen_clicks)
    is_windows_stcuked = [0] * len(shimen_clicks)
    prev_images = [im.capture_region(region=(int(x), int(y), int(x1-x), int(y1-y))) for x, y, x1, y1 in shimen_clicks]

    time.sleep(20)

    while not all(is_window_finished):
        for i, area in enumerate(shimen_clicks):
            if is_window_finished[i]:
                continue

            left, top, right, bottom = area
            area_width = right - left
            area_height = bottom - top
            screen = im.capture_region(region=(left, top, area_width, area_height))
            stuck_result = im.has_region_changed(prev_images[i], screen, threshold=0.80)

            if stuck_result:
                if not is_windows_stcuked[i]:  # First time detecting a stuck
                    is_windows_stcuked[i] = True
                else:  # Second consecutive stuck detection
                    random_click_mouse((left, top, right, bottom), quick_mode=True)
                    is_windows_stcuked[i] = False  # Reset after clicking

            prev_images[i] = screen

        # Checks the secondary completion (jiuzhuan)
        # is_window_finished = click_secondary_panel()
        
        time.sleep(random.uniform(2, 5))
        
        for i, window in enumerate(window_capture_areas_):
            shimen_completes = im.find_multiple_icons_on_screen(shimen_complete_checks, screen_area=window, threshold=0.85)
            if shimen_completes[1]:
                random_click_mouse(shimen_completes[1])
            if any(shimen_completes):
                is_window_finished[i] = True

        time.sleep(random.uniform(30, 40))  # Allows time before the next iteration


    time.sleep(random.uniform(10,20))
    shimen_completed_clicks = im.find_all_icons(shimen_completed_click_path, threshold=0.9)
    for shimen_completed_click in shimen_completed_clicks:
        random_click_mouse(shimen_completed_click) 
    
    time.sleep(random.uniform(2,5))
    quit_shimens = im.find_all_icons(quit_shimen_path)
    for quit_shimen in quit_shimens:
        random_click_mouse(quit_shimen)

    for window in window_capture_areas_:
        all_item_clicked = False
        memorize_click_pos = None
        while not all_item_clicked:
            click = im.find_icon_on_screen(use_item_path, screen_area=window, threshold=0.9)
            if click == None:
                all_item_clicked = True
                continue
            
            if not memorize_click_pos:
                random_click_mouse(click)
                memorize_click_pos = True
            else:
                click_mouse()
            time.sleep(random.uniform(0.3,0.7))


def go_to_quest(template_path, mask_path=None, threshold=0.95):
    click_activity_panel()
    time.sleep(3)
    to_completes = im.find_all_icons(template_path,mask_path=mask_path, threshold=threshold)

    for top_left_x, top_left_y, _, _ in to_completes:
        button_left = top_left_x + button_relative_area_[0]
        button_top = top_left_y + button_relative_area_[1]
        button_right = top_left_x + button_relative_area_[2]
        button_bottom = top_left_y + button_relative_area_[3]

        # Perform the click specifically on the button
        random_click_mouse((button_left, button_top, button_right, button_bottom))


# ------------------------------BAOTU related --------------------------------------------
# def choose_baotu_in_inventory():
#     inventory_clicks = im.find_all_icons(inventory_path, threshold=0.85)
#     for click in inventory_clicks:
#         random_click_mouse(click)
    
#     x, y1, x1, y = inventory_area_
#     for window in window_capture_areas_:
#         print("working on window ", window)
#         topx, topy, _, _ = window
#         start_x = topx + x
#         start_y = topy + y
#         end_x = topx + x1
#         end_y = topy + y1

#         # random_start_y = random.uniform(start_y - 20, (start_y-end_y)/2 + end_y)
#         # random_end_y   = random.uniform(end_y + 20,(start_y-end_y)/2 + end_y)
#         # print(random_start_y, random_end_y)

#         baotu_found = False

#         drag_counter = 0
#         while not baotu_found:
#             result = im.find_icon_on_screen(baotu_item_path, screen_area=window, threshold=0.85)

#             if result != None:
#                 random_click_mouse(result, double_click=True)
#                 baotu_found = True
#                 continue

#             random_start_y = random.uniform(start_y - 20, (start_y-end_y)/2 + end_y)
#             random_end_y   = random.uniform(end_y + 20,(start_y-end_y)/2 + end_y)
#             print(random_start_y, random_end_y)
            
#             if drag_counter <= 10:
#                 drag_mouse_vertically((start_x, random_start_y, end_x, random_end_y))
#                 time.sleep(random.uniform(0.5,1.5))
#                 drag_counter += 1

#             elif drag_counter <= 20:
#                 drag_mouse_vertically((start_x, random_end_y, end_x, random_start_y))
#                 time.sleep(random.uniform(0.5,1.5))
#                 drag_counter += 1
            
#             elif drag_counter > 20:
#                 print("baotu not found or some bugs appeared")
#                 break


# def dig_baotu():
#     baotu_task_icons = [{"template_path": use_item_path, "filter_range": None},
#                         {"template_path": auto_battle_path, "filter_range": None},
#                        ]

#     # Initial window status
#     window_status = {i: {"state": "waiting", "counter": 0} for i in range(5)}  # Complete, Battle, Waiting

#     # Define maximum retries for windows
#     MAX_RETRIES = 3

#     while any(window["counter"] < MAX_RETRIES for window in window_status.values()):
#         for i in window_status:
#             # Get the screen region for the current window
#             results = im.find_multiple_icons_on_screen(baotu_task_icons, screen_area=window_capture_areas_[i])
            
            
#             # Process if `use_item` icon is found
#             if results[0]:
#                 random_click_mouse(results[0])  # Click the `use_item` icon
#                 window_status[i]["counter"] = 0  # Reset counter when action is taken

#             # Process if `auto_battle` icon is found
#             elif results[1]:
#                 window_status[i]["state"] = "in_battle"  # Mark as in battle
#                 window_status[i]["counter"] = 0  # Reset counter in battle state

#             # If no icons found, increment the counter if the window is not in a valid state
#             elif all(result == None for result in results):
#                 window_status[i]["counter"] += 1

#             # If the window has been checked multiple times without progress, mark as completed
#             if window_status[i]["counter"] >= MAX_RETRIES:
#                 window_status[i]["state"] = "completed"
#                 print(f"Window {i} task is completed.")
            
#             time.sleep(random.uniform(0.4,0.7))
#         # Sleep after each check to simulate delay
#         time.sleep(random.uniform(7, 14))  # Adjust the sleep time to simulate human behavior

#         print("Checking windows progress...")  # Optional log message

def perform_baotu():
    go_to_quest(baotu_path,mask_path=mask_path_, threshold=0.95)   
    time.sleep(3)
    selection_clicks = click_selection_menu(expected_num=window_capture_areas_len)
    for click in selection_clicks:
        random_click_mouse(click)

    # baotu_clicks = im.find_all_icons(baotu_clicks_path, threshold=0.63)
    # baotu_clicks = [(int(x), int(y), int(x1), int(y1)) for x,y,x1,y1 in baotu_clicks]
    # print(baotu_clicks)
    # for i in baotu_clicks:
    #     random_click_mouse(i)

    baotu_clicks = []
    for window in window_capture_areas_:
        baotu_click = im.find_filtered_icons(baotu_clicks_path,screen_area=window, threshold=0.75)
        random_click_mouse(baotu_click, double_click=True)
        baotu_clicks.append(baotu_click)
    
    prev_images = [im.capture_region(region=(x, y, x1-x, y1-y)) for x,y,x1,y1 in baotu_clicks]
    time.sleep(30)
    is_all_window_completed = False
    is_window_completed = [False] * 5
    # baotu_completion_checks = [baotu_clicks_path, auto_battle_path]
    baotu_completion_checks = [{"template_path": baotu_clicks_path, "filter_range": YELLOW_COLOR_RANGE},
                              {"template_path": auto_battle_path, "filter_range": None},
                              {"template_path": shimen_completed_2_path, "filter_range": None}]

    while not is_all_window_completed:
        for i, (x, y, x1, y1) in enumerate(baotu_clicks):
            if is_window_completed[i]:
                print(f"window{i} is already completed")
                continue

            is_working = im.find_icon_on_screen(auto_battle_path, screen_area=window_capture_areas_[i],  threshold=0.50)
            if is_working:
                print(f"window{i} is in battle")
                # time.sleep(random.uniform(1,3))
                continue

            click_width = x1-x
            click_height = y1-y
            current_image = im.capture_region((x,y,click_width,click_height))
            is_stucked = im.has_region_changed(prev_images[i], current_image)
            if is_stucked:
                random_click_mouse((x,y,x1,y1))

            print(x, "  stucked!!" if is_stucked else "   not stucked!!",)
            prev_images[i] = current_image

        time.sleep(random.uniform(40,60))
        # is_window_completed = click_secondary_panel()

        for i, area in enumerate(window_capture_areas_):
            check_completion = im.find_multiple_icons_on_screen(baotu_completion_checks, screen_area=area, threshold=0.68)
            print("baotu checks", check_completion)
            if check_completion[2]:
                random_click_mouse(check_completion[2])

            if check_completion[0]==None and check_completion[1]==None:
                is_window_completed[i] = True

        if all(is_window_completed):
            is_all_window_completed = True
            print("baotu completed")
        else:
            print("not yet done")
        time.sleep(5)
    
    # click_until_end(use_item_path,clicking_delay=(5,10))
    choose_baotu_in_inventory()
    time.sleep(random.uniform(10,15))
    dig_baotu()

def perform_mijing():
    go_to_quest(mijing_path,mask_path=mask_path_, threshold=0.93)
    # time.sleep(3)
    selection_clicks = click_selection_menu(len(window_capture_areas_))
    for click in selection_clicks:
        random_click_mouse(click)

    mijing_continue_battles = im.find_all_icons(mijing_continue_battle_path)
    for mijing_continue_battle in mijing_continue_battles:
        random_click_mouse(mijing_continue_battle)

    mijing_clicks = []
    prev_images = []
    for window in window_capture_areas_:
        mijing_click = im.find_filtered_icons(mijing_click_path, screen_area=window, threshold=0.70)
        random_click_mouse(mijing_click)
        # mijing_clicks = [(int(x), int(y), int(x1), int(y1)) for x,y,x1,y1 in mijing_clicks]
        x,y,x1,y1 = mijing_click
        prev_images.append(im.capture_region(region=(x, y, x1-x, y1-y)))
        mijing_clicks.append(mijing_click)

    # prev_images = [im.capture_region(region=(x, y, x1-x, y1-y)) for x,y,x1,y1 in mijing_clicks]
    time.sleep(30)

    is_all_window_completed = False
    window_process_checks = [{"template_path": selection_menu_path, "filter_range": None}, 
                             {"template_path": auto_battle_path, "filter_range": None},
                            ]

    window_match_count = {i:{"count":0, "in_battle":False} for i in range(len(window_capture_areas_))}

    while not is_all_window_completed:
        for i, (x, y, x1, y1) in enumerate(mijing_clicks):
            if (window_match_count[i]["count"] >= 2) or (window_match_count[i]["in_battle"]):
                print("NO NEED to check window ", i)
                continue  

            click_width = x1-x
            click_height = y1-y
            current_image = im.capture_region((x,y,click_width,click_height))
            is_stucked = im.has_region_changed(prev_images[i], current_image)
            if is_stucked:
                random_click_mouse((x,y,x1,y1))

            print("window ", i , "  stucked!!" if is_stucked else "   not stucked!!",)
            prev_images[i] = current_image
        
        time.sleep(random.uniform(60,61))

        for i, window in enumerate(window_capture_areas_):
            # 0:selection menu, 1: in battle
            results = im.find_multiple_icons_on_screen(window_process_checks, screen_area=window)
            print("checking COMPLETIONS: ", results)
            
            if results[0] != None:
                window_match_count[i]["count"] += 1
                print("windows count ",  window_match_count[i]["count"])

                if window_match_count[i]["count"] >= 2:
                    continue 
                else:
                    x, y,_,_ = results[0]
                    pos = calculate_selection_menu_displace(x,y)
                    random_click_mouse(pos)
            
            if results[1] != None:
                window_match_count[i]["in_battle"] = True
                print(f"widow{i} is in battle")
            else:
                window_match_count[i]["in_battle"] = False 
                print(f"widow{i} NOT in battle")



        # to_completes = im.find_all_icons(selection_menu_path)
        # for i in to_completes:
        #     tx, ty, _, _ = i

        #     # Get the window index where the click is located
        #     window_idx = get_window_area(tx, ty)
        #     print("window_idx found ",window_idx)

        #     if window_idx is not None:
        #         window_match_count[window_idx] += 1
        #         print("windows count ", window_match_count)

        #         if window_match_count[window_idx] >= 2:
        #             continue 

        if all(count["count"] >= 2 for count in window_match_count.values()):
            print("All windows completed, task done!")
            mijing_quits = im.find_all_icons(mijing_quit_path)
            for i in mijing_quits:
                random_click_mouse(i, double_click=True)
            is_all_window_completed = True

def perform_yabiao():
    go_to_quest(yabiao_path,mask_path=mask_path_, threshold=0.93)

    time.sleep(3)
    window_completion = [0] * 5
    is_yabiao_completed = False
    while not is_yabiao_completed:
        to_completes = click_selection_menu()
        for i in to_completes:
            random_click_mouse(i)
            x,y,_,_ = i
            window_idx = get_window_area(x,y)
            window_completion[window_idx] += 1
        
        yabiao_confirms = im.find_all_icons(yabiao_confirm_path, threshold=0.90)
        for yabiao_confirm in yabiao_confirms:
            random_click_mouse(yabiao_confirm)
        # for i in to_completes:
        #     x,y,_,_ = i
        #     window_idx = get_window_area(x,y)
        #     window_completion[window_idx] += 1
        
        if all(counter >= 3 for counter in window_completion):
            is_yabiao_completed = True
        
        time.sleep(random.uniform(40,80))
    
    time.sleep(random.uniform(80,120))
    complete_clicks = im.find_all_icons(yabiao_complete_2_path)
    for click in complete_clicks:
        random_click_mouse(click)


#-----------------------------------------Dungeon Related------------------------------------------------------------
def find_icon_in_dungeon(template_path):
    return im.find_icon_on_screen(template_path, screen_area=(WINDOW_FOCUS_WIDTH, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

def wait_until_click(template_path, click_area= None):
    icon_found = None
    exhausted_counter = 0
    while icon_found == None:
        icon_found = find_icon_in_dungeon(template_path)

        exhausted_counter += 1
        if exhausted_counter >= 20:
            return

        time.sleep(random.uniform(1,2))

    if click_area != None:
        icon_found = click_area
    # result = find_icon_on_screen(skip_cinematic_path)
    print(icon_found)
    random_click_mouse(icon_found)
    time.sleep(random.uniform(3,5))

in_dungeon_paths_ = [{"template_path": skip_cinematic_path, "filter_range": None},
                     {"template_path": selection_menu_path, "filter_range": None},
                     {"template_path": go_battle_path, "filter_range": None},
                     {"template_path": dungeron_click_continue_path, "filter_range": None},
                     {"template_path": in_battle_icon_path, "filter_range": None},
                     {"template_path": dungeon_completed_path, "filter_range": None},
                    ]

def dungeon_process():
    is_dungeon_completed = False
    while not is_dungeon_completed:
        dungeon_results = im.find_multiple_icons_on_screen(in_dungeon_paths_, screen_area=window_capture_areas_[0], threshold=0.78)
        print(dungeon_results)
        for i, result in enumerate(dungeon_results):
            if result == None:
                continue
            if i == 0:
                random_click_mouse(result)
            elif i == 1:
                random_click_mouse((475, 360, 600, 380))
            elif i == 2:
                random_click_mouse((500, 130, 625, 170))
            elif i == 3:
                random_click_mouse(result)
            elif i == 4:
                time.sleep(random.uniform(20,30))
                while (im.find_icon_on_screen(in_battle_icon_path) != None):
                    print("battle is not finished yet")
                    time.sleep(random.uniform(5,10))
            elif i == 5:
                random_click_mouse((500, 130, 625, 170))
                is_dungeon_completed = True
            print("for done")
            break
        print("while done")
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

def perform_dungeons(elite=False):
    dungeon_counter = 0
    elite_dungeon_counter = 0

    while True:
        activity_click = im.find_icon_on_screen(activity_panel_path, screen_area=window_capture_areas_[0])
        random_click_mouse(activity_click)
        time.sleep(random.uniform(2,3))
        dungeon_pos = im.find_multiple_icons_on_screen(dungeon_paths_, mask_path=mask_path_, screen_area=window_capture_areas_[0], threshold=0.89)
        print("dungeon located at: ", dungeon_pos)

        all_none = True

        for i, pos in enumerate(dungeon_pos):
            if pos == None:
                print(f"window {i} not found!!!")
                continue

            top_left_x, top_left_y, _, _ = pos
            all_none = False
            break

        if all_none:
            break

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

        if elite and elite_dungeon_counter <= 1:
            elite_dungeon_panel = im.find_icon_on_screen(elite_dungeon_panel_path, screen_area=window_capture_areas_[0])
            random_click_mouse(elite_dungeon_panel)
            time.sleep(random.uniform(0.1,0.3))

            dungeon_enter_clicks = im.find_all_icons(dungeon_enter_path, screen_area=window_capture_areas_[0],threshold=0.85)
            random_click_mouse(dungeon_enter_clicks[elite_dungeon_counter])
            time.sleep(random.uniform(0.1,0.3))

            for window in window_capture_areas_[1:]:
                elite_dungeon_ready = im.find_icon_on_screen(elite_dungeon_ready_path, screen_area=window)
                random_click_mouse(elite_dungeon_ready)
                time.sleep(random.uniform(0.1,0.3))

            elite_dungeon_counter += 1
            time.sleep(random.uniform(5,10))
            dungeon_process()
            continue

        dungeon_enter_clicks = im.find_all_icons(dungeon_enter_path, screen_area=window_capture_areas_[0],threshold=0.85)
        random_click_mouse(dungeon_enter_clicks[dungeon_counter])
        dungeon_counter += 1
        time.sleep(random.uniform(5,10))
        dungeon_process()

def perform_zhuagui(rounds=5):
    activity_click = im.find_icon_on_screen(activity_panel_path, screen_area=window_capture_areas_[0])
    random_click_mouse(activity_click)
    zhuagui_click = im.find_icon_on_screen(zhuagui_path, mask_path=mask_path_, screen_area=window_capture_areas_[0], threshold=0.9)
    top_left_x, top_left_y, _, _ = zhuagui_click

    button_left = top_left_x + button_relative_area_[0]
    button_top = top_left_y + button_relative_area_[1]
    button_right = top_left_x + button_relative_area_[2]
    button_bottom = top_left_y + button_relative_area_[3]

    # Perform the click specifically on the button
    random_click_mouse((button_left, button_top, button_right, button_bottom))

    zhuagui_counter = 0
    time.sleep(7)
    while zhuagui_counter < rounds:
        selection_menu_click =click_selection_menu()
        random_click_mouse(*selection_menu_click)
        time.sleep(3)
        random_click_mouse((500, 185, 626, 231),double_click=True)

        is_cycle_done = False
        while not is_cycle_done:
            time.sleep(random.uniform(30,50))    
            complete_click = im.find_icon_on_screen(zhuagui_continue_path, screen_area=window_capture_areas_[0])
            if complete_click != None:
                random_click_mouse(complete_click)
                zhuagui_counter += 1
                is_cycle_done = True

        time.sleep(random.uniform(5,8))


def create_party():
    captain_window = window_capture_areas_[0]
    random_click_mouse(party_panel)
    time.sleep(random.uniform(0.1,0.3))
    
    recruit_click = im.find_icon_on_screen(recruit_button_path,screen_area=captain_window)
    random_click_mouse(recruit_click)
    time.sleep(random.uniform(0.1,0.3))

    my_recruit_button_click = im.find_icon_on_screen(my_recruit_button_path,screen_area=captain_window)
    random_click_mouse(my_recruit_button_click)
    time.sleep(random.uniform(0.1,0.3))

    click_to_party_click = im.find_icon_on_screen(click_to_party_path,screen_area=captain_window)
    random_click_mouse(click_to_party_click)
    time.sleep(random.uniform(0.1,0.3))

    for window in window_capture_areas_[1:]:
        clicks = im.find_icon_on_screen(party_accept_path,screen_area=window)
        random_click_mouse(clicks, quick_mode=True)
    
    party_panel_close_click = im.find_icon_on_screen(party_panel_close_path,screen_area=captain_window)
    random_click_mouse(party_panel_close_click)
    time.sleep(random.uniform(0.1,0.3))

    party_panel_close_click = im.find_icon_on_screen(party_panel_close_path,screen_area=captain_window)
    random_click_mouse(party_panel_close_click)
    time.sleep(random.uniform(0.1,0.3))




def perform_qiyuan():
    go_to_quest(qiyuan_path,mask_path=mask_path_, threshold=0.95)
     
    qiyuan_completion = [False] * len(window_capture_areas_)
    x,y,x1,y1 = qiyuan_area_
    while not all(qiyuan_completion):
        for i, area in enumerate(window_capture_areas_):
            check_progress = im.find_icon_on_screen(qiyuan_complete_check_path, screen_area=area, threshold=0.9)

            if check_progress:
                top_l, top_r, _, _ = area
                
                # clicking_pos_x = random.uniform(top_l+x, top_l+x1)
                # clicking_pos_y = random.uniform(top_r+y, top_r+y1)
                random_click_mouse((top_l+x, top_r+y, top_l+x1, top_r+y1))
            else:
                qiyuan_completion[i] = True
        
        if all(qiyuan_completion):
            break

if __name__ == "__main__":

    """
    current game window size is 653, 517
    adjusted size 669 556
    """

    # Get predefined positions
    positions, window_positions = get_window_positions(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT)

    window_capture_areas_len = len(window_capture_areas_)
    # print(window_capture_areas)
    # Find all game windows
    game_windows = enum_windows_by_title("梦幻西游：时空")

    # if len(game_windows) >= 5:
    #     # Move windows to their respective positions
    #     move_windows_to_positions(game_windows[:5], positions, WINDOW_WIDTH, WINDOW_HEIGHT)
    # else:
    #     print(f"Found only {len(game_windows)} game windows. Make sure 5 instances are running.")
    
    # print("aaa", window_positions)
    
    # random_click_mouse(455, 284, 598, 301) # dungeon_panel
    # random_click_mouse(143, 392, 209, 408) # select_dungeon
    # random_click_mouse(505, 188, 622, 204) # skip_cinematics
    time.sleep(2.0)
    # random_click_mouse(500, 130, 625, 170) # going_to_battle
    # random_click_mouse(475, 360, 600, 380) # battle

    # in_battle_icon_path = "img_templates/in_battle.png"

    # while (find_icon_on_screen(in_battle_icon_path) != None):
    #     print("battle is not finished yet")
    #     time.sleep(30)

    # perform_shimen()
    # perform_baotu()
    # perform_mijing()
    # perform_yabiao()
    # create_party()
    # perform_dungeons(elite=False)
    # perform_zhuagui(30)
    # perform_qiyuan()
    
    # click_secondary_panel()
    choose_baotu_in_inventory()
    time.sleep(10)
    dig_baotu()

    # result = im.find_icon_on_screen(a6_path, mask_path=mask_path_, screen_area=None)


# in_dungeon_paths_ = [{"template_path": selection_menu_path, "filter_range": None},
#                      {"template_path": mengjing_path, "filter_range": YELLOW_COLOR_RANGE},
#                      {"template_path": in_battle_icon_path, "filter_range": None},
#                     ]

# def dungeon_process():
#     is_dungeon_completed = False
#     while True:
#         dungeon_results, vals = im.find_multiple_icons_on_screen(in_dungeon_paths_, screen_area=window_capture_areas_[0], threshold=0.78)
#         logger.info(f"Dungeon processes {dungeon_results} with {vals}")
#         for i, result in enumerate(dungeon_results):
#             if result == None:
#                 continue
#             if i == 0:
#                 logger.info("Skipping dungeon cinematic")
#                 random_click_mouse(result)
#             elif i == 1:
#                 logger.info("Clicking selection menu")
#                 random_click_mouse((475, 360, 600, 380))
#             elif i == 2:
#                 logger.info("Battle detected")
#                 time.sleep(random.uniform(20,30))
#                 while (im.find_icon_on_screen(in_battle_icon_path)[0] != None):
#                     print("battle is not finished yet")
#                     time.sleep(random.uniform(5,10))
#             break

#         logger.info("End of dungeon process while loop")
#         time.sleep(random.uniform(3,5))

# dungeon_process()