from abc import ABC, abstractmethod
import json
import os
import random
import re
import time
from difflib import SequenceMatcher
import pygetwindow as gw
import numpy as np
from get_windows import enum_windows_by_title, get_window_positions, move_windows_to_positions
import helpers as helper_actions
from mouse_action import random_click_mouse, click_mouse, drag_mouse_vertically, scratch_horizontally
import image_matching as im
from config import *
from helpers import *
from logger import logger

class state(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def execute(self):
        pass

    def get_next_state(self):
        return self.next_state


STATE_REGISTRY = {}

def register_state(cls):
    """Decorator to register states automatically."""
    STATE_REGISTRY[cls.__name__] = cls
    return cls

@register_state
class perform_shimen(state):

    def execute(self):
        shimen_complete_checks = [{"template_path": shimen_completed_click_path, "filter_range": None},
                                  {"template_path": shimen_completed_2_path, "filter_range": None}]

        shimen_clicks = []
        logger.info("Finding Shimen clicking areas")
        for window in window_capture_areas_:
            shimen_click, val = im.find_filtered_icons(shimen_clicking_area_path,screen_area=window)
            logger.info(f"Found Shimen area at {shimen_click} value: {val}")
            random_click_mouse(shimen_click)
            shimen_clicks.append(shimen_click)
        
        time.sleep(random.uniform(1,3))
        logger.info("Shimen accepting phase.........")
        to_completes,_ = im.find_icon_each_window(shimen_accept_path, threshold=0.90)

        for i in to_completes:
            random_click_mouse(i)

        is_window_finished = [False] * len(shimen_clicks)
        is_windows_stcuked = [0] * len(shimen_clicks)
        prev_images = im.capture_regions(shimen_clicks)
        time.sleep(20)

        while not all(is_window_finished):
            for i, (left, top, right, bottom) in enumerate(shimen_clicks):
                if is_window_finished[i]:
                    continue  # Skip if already finished

                # Check for completion first
                shimen_completes, vals = im.find_multiple_icons_on_screen(shimen_complete_checks, screen_area=window_capture_areas_[i], threshold=0.85)
                logger.info(f"Window {i} Shimen checks: {shimen_completes} with {vals}")

                if shimen_completes[1]:  # If specific completion icon is found
                    logger.info("Clicking the extra panels when shimen completes")
                    random_click_mouse(shimen_completes[1])

                if shimen_completes[0]:  # If any completion icon is detected
                    is_window_finished[i] = True
                    logger.info(f"Window {i} marked as finished.")
                    continue  # Skip stuck check if window is now finished

                # If not completed, check for stuck state
                logger.info("Chekcing if Shimen is stucked")
                area_width = right - left
                area_height = bottom - top
                screen = im.capture_region(region=(left, top, area_width, area_height))
                stuck_result,_ = im.has_region_changed(prev_images[i], screen, threshold=0.80)

                if stuck_result:
                    is_windows_stcuked[i] += 1  # Increment stuck counter
                    logger.info(f"Window {i} is stuck. Counter: {is_windows_stcuked[i]}")

                    if is_windows_stcuked[i] >= 2:  # If stuck twice in a row, click to unstick
                        logger.warning(f"Window {i} is stuck again. Trying to resolve the issue...")
                        random_click_mouse((left, top, right, bottom), quick_mode=True)
                        is_windows_stcuked[i] = 0  # Reset after unstick action

                elif is_windows_stcuked[i] != 0:  # Only reset if counter was previously incremented
                    is_windows_stcuked[i] = 0
                    logger.info(f"Window {i} is no longer stuck. Counter reset.")

                prev_images[i] = screen  # Update previous image for next iteration

            time.sleep(random.uniform(30, 40))  # Delay before next iteration

        
        logger.info("All windows have finished the shimen task")
        time.sleep(random.uniform(10,20))

        shimen_completed_2_clicks,_ = im.find_icon_each_window(shimen_completed_2_path, threshold=0.80)
        for shimen_completed_2_click in shimen_completed_2_clicks:
            if shimen_completed_2_click is not None:
                random_click_mouse(shimen_completed_2_click) 

        shimen_completed_clicks,_ = im.find_icon_each_window(shimen_completed_click_path, threshold=0.80)
        for shimen_completed_click in shimen_completed_clicks:
            random_click_mouse(shimen_completed_click) 
        
        time.sleep(random.uniform(2,5))
        logger.info("Quitting Shimen..........")
        quit_shimens,_ = im.find_icon_each_window(quit_shimen_path)
        for quit_shimen in quit_shimens:
            random_click_mouse(quit_shimen)

        click_reward_items()


@register_state
class perform_baotu(state):

    def execute(self):
        go_to_quest(baotu_path, mask_path=mask_path_, threshold=0.85)
        time.sleep(3)

        selection_clicks = click_selection_menu(expected_num=len(window_capture_areas_),
                                                previous_task=baotu_path,
                                                auto_recovery=True)
        for click in selection_clicks:
            random_click_mouse(click)

        time.sleep(30)

        # Define window states and counters
        window_states = [{"state": "waiting", "stuck_counter": 0} for _ in range(5)]
        baotu_completion_checks = [{"template_path": baotu_clicks_path, "filter_range": YELLOW_COLOR_RANGE},
                                   {"template_path": auto_battle_path, "filter_range": None},
                                   {"template_path": shimen_completed_2_path, "filter_range": None}]

        while not all(state["state"] == "completed" for state in window_states):
            for i, window in enumerate(window_capture_areas_):
                if window_states[i]["state"] == "completed":
                    logger.info(f"Window {i} is already completed.")
                    continue

                # If both completion checks are None, mark window as completed and skip other checks
                check_completion, vals = im.find_multiple_icons_on_screen(baotu_completion_checks, screen_area=window, threshold=0.68)
                logger.info(f"Window {i} baotu checks: {check_completion} with {vals}")

                # Handle the extra button click when Baotu completes
                if check_completion[2]:
                    logger.info("clicking extra button when Baotu completes")
                    random_click_mouse(check_completion[2])

                if check_completion[0] is None and check_completion[1] is None:
                    window_states[i]["state"] = "completed"
                    logger.info(f"Window {i} marked as completed.")
                    continue  # Skip further checks and move to the next window

                # Handle the window stuck state
                if check_completion[0]:
                    window_states[i]["stuck_counter"] += 1
                    if window_states[i]["stuck_counter"] >= 3:
                        random_click_mouse(check_completion[0])  # Unstick the window
                        window_states[i]["stuck_counter"] = 0  # Reset stuck counter
                        window_states[i]["state"] = "unstuck"  # Transition to unstuck state
                else:
                    window_states[i]["stuck_counter"] = 0  # Reset if not stuck

                # If window is in battle
                if check_completion[1]:  # Window is in battle
                    window_states[i]["state"] = "in_battle"
                    logger.info(f"Window {i} is in battle.")
                    continue  # Skip stuck check if in battle

            time.sleep(random.uniform(40, 60))  # Sleep between iterations

        choose_baotu_in_inventory()
        time.sleep(random.uniform(10, 15))
        dig_baotu()


@register_state
class perform_mijing(state):

    def execute(self):
        go_to_quest(mijing_path,mask_path=mask_path_, threshold=0.85)
        time.sleep(random.uniform(2,5))

        selection_clicks = click_selection_menu(expected_num=len(window_capture_areas_),
                                                previous_task=mijing_path,
                                                auto_recovery=True)
        for click in selection_clicks:
            random_click_mouse(click)

        if im.find_icon_on_screen(mijing_enter_path)[0] != None:
            logger.info("Mijing found choices, selecting......")
            clicks_mijing_enter, vals = im.find_icon_each_window(mijing_enter_path)
            for click, val in zip(clicks_mijing_enter, vals):
                logger.info(f"At location {click} found value: {val}")
                random_click_mouse(click)
            
            time.sleep(random.uniform(2,5))

            logger.info("Mijing Confirming choices.............")
            clicks_mijing_confirm, vals = im.find_icon_each_window(mijing_confirm_path)
            for click, val in zip(clicks_mijing_confirm, vals):
                logger.info(f"At location {click} found value: {val}")
                random_click_mouse(click)

            time.sleep(random.uniform(2,5))

        logger.info("Clicking Mijing continue battle.........")
        mijing_continue_battles,_ = im.find_icon_each_window(mijing_continue_battle_path)
        for mijing_continue_battle in mijing_continue_battles:
            random_click_mouse(mijing_continue_battle)

        mijing_clicks = []
        for window in window_capture_areas_:
            logger.info("Fiding Mijing clicking areas")
            mijing_click, val = im.find_filtered_icons(mijing_click_path, screen_area=window, threshold=0.70)
            logger.info(f"Found Mijing area at {mijing_click} value: {val}")
            random_click_mouse(mijing_click)

            mijing_clicks.append(mijing_click)

        prev_images = im.capture_regions(mijing_clicks)

        # prev_images = [im.capture_region(region=(x, y, x1-x, y1-y)) for x,y,x1,y1 in mijing_clicks]
        time.sleep(30)

        is_all_window_completed = False
        window_process_checks = [{"template_path": selection_menu_path, "filter_range": None}, 
                                {"template_path": auto_battle_path, "filter_range": None},
                                {"template_path": defeated_path, "filter_range": None}
                                ]

        window_match_count = {i:{"count":0, "in_battle":False} for i in range(len(window_capture_areas_))}

        while not is_all_window_completed:
            for i, (x, y, x1, y1) in enumerate(mijing_clicks):
                # Skip if the window has completed Mijing_MAX_TRY_OUTS cycles
                if window_match_count[i]["count"] >= Mijing_MAX_TRY_OUTS:
                    logger.info(f"Window {i} is already completed.")
                    continue

                # Check window status (battle or completion)
                results, vals = im.find_multiple_icons_on_screen(window_process_checks, screen_area=window_capture_areas_[i])
                logger.info(f"Window {i} status check: {results} with {vals}")

                # 1. Prioritize battle state
                if results[1]:  # In battle detected
                    logger.info(f"Window {i} is in battle.")
                    continue  # No need to check completion or stuck state

                if results[2]:
                    logger.info(f"window {i} is Defeated marks as done")
                    window_match_count[i]["count"] = Mijing_MAX_TRY_OUTS
                    random_click_mouse(results[2])
                    continue

                # 2. Handle completion status
                if results[0]:  # Selection menu detected (indicating completion)
                    if window_match_count[i]["count"] < Mijing_MAX_TRY_OUTS:
                        # First or second completion detection
                        window_match_count[i]["count"] += 1
                        logger.info(f"Window {i} completion count: {window_match_count[i]['count']}")

                        if window_match_count[i]["count"] == Mijing_MAX_TRY_OUTS:
                            logger.info(f"Window {i} has fully completed its task.")
                        else:
                            # Perform action to proceed if not fully completed
                            x_sel, y_sel, _, _ = results[0]
                            pos = calculate_selection_menu_displace(x_sel, y_sel)
                            random_click_mouse(pos)
                    continue  # Skip stuck check if selection menu detected

                # 3. Check for stuck state if not in battle or completed
                logger.info("Checking if Mijing stucked.....")
                click_width = x1 - x
                click_height = y1 - y
                current_image = im.capture_region((x, y, click_width, click_height))
                is_stucked,_ = im.has_region_changed(prev_images[i], current_image)

                if is_stucked:
                    logger.info(f"Window {i} is stuck, attempting to unstick.")
                    random_click_mouse((x, y, x1, y1))
                else:
                    logger.info(f"Window {i} is not stuck.")

                prev_images[i] = current_image  # Update for next comparison
         
            # Check if all windows have completed their tasks
            if all(count["count"] >= Mijing_MAX_TRY_OUTS for count in window_match_count.values()):
                logger.info("All windows completed, task done!")
                mijing_quits,_ = im.find_icon_each_window(mijing_quit_path)
                for quit_click in mijing_quits:
                    random_click_mouse(quit_click, double_click=True)
                is_all_window_completed = True
            else:
                time.sleep(random.uniform(60, 61))  # Delay before next check

        click_reward_items()

@register_state
class perform_yabiao(state):

    def execute(self):
        go_to_quest(yabiao_path,mask_path=mask_path_, threshold=0.85)

        time.sleep(3)
        window_completion = [0] * 5
        is_yabiao_completed = False
        while not is_yabiao_completed:
            to_completes = click_selection_menu(expected_num=0)

            if not to_completes:
                logger.info("No selection menu found, skip clicking and counting")
                time.sleep(random.uniform(60,80))
                continue

            for i in to_completes:
                random_click_mouse(i)
                x,y,_,_ = i
                window_idx = get_window_area(x,y)
                window_completion[window_idx] += 1
            
            logger.info("Checking Yabiao confirms.......")
            yabiao_confirms,_ = im.find_icon_each_window(yabiao_confirm_path, threshold=0.90)
            for yabiao_confirm in yabiao_confirms:
                random_click_mouse(yabiao_confirm)
            # for i in to_completes:
            #     x,y,_,_ = i
            #     window_idx = get_window_area(x,y)
            #     window_completion[window_idx] += 1
            
            if all(counter >= 3 for counter in window_completion):
                is_yabiao_completed = True
            
            time.sleep(random.uniform(40,80))
        
        time.sleep(random.uniform(200,250))
        logger.info("Finishing up Yabiao!!")

        clicks,_ = im.find_icon_each_window(yabiao_complete_2_path)

        for click in clicks:
            random_click_mouse(click)


@register_state
class perform_create_party(state):

    def execute(self):
        captain_window = window_capture_areas_[0]
        random_click_mouse(party_panel)
        time.sleep(random.uniform(0.1,0.3))
        
        recruit_click,_ = im.find_icon_on_screen(recruit_button_path,screen_area=captain_window)
        random_click_mouse(recruit_click)
        time.sleep(random.uniform(0.1,0.3))

        recruit_hall_click,_ = im.find_icon_on_screen(recruit_hall_path,screen_area=captain_window)
        random_click_mouse(recruit_hall_click)
        time.sleep(random.uniform(0.5,1.0))

        my_party_recruit_click,_ = im.find_icon_on_screen(my_party_recruit_path, screen_area=captain_window)
        random_click_mouse(my_party_recruit_click)
        time.sleep(random.uniform(0.5,1.0))

        click_to_party_click,_ = im.find_icon_on_screen(click_to_party_path,screen_area=captain_window)
        random_click_mouse(click_to_party_click)
        time.sleep(random.uniform(0.1,0.3))

        for window in window_capture_areas_[1:]:
            clicks,_ = im.find_icon_on_screen(party_accept_path,screen_area=window)
            random_click_mouse(clicks, quick_mode=True)
        
        party_panel_close_click,_ = im.find_icon_on_screen(party_panel_close_path,screen_area=captain_window)
        random_click_mouse(party_panel_close_click)
        time.sleep(random.uniform(0.1,0.3))

        party_recruit_close_click,_ = im.find_icon_on_screen(party_recruit_close_path,screen_area=captain_window)
        random_click_mouse(party_recruit_close_click)
        time.sleep(random.uniform(0.1,0.3))

        recruit_hall_close_click,_ = im.find_icon_on_screen(recruit_hall_close_path,screen_area=captain_window)
        random_click_mouse(recruit_hall_close_click)
        time.sleep(random.uniform(0.1,0.3))

        # party_panel_close_click,_ = im.find_icon_on_screen(party_panel_close_path,screen_area=captain_window)
        # random_click_mouse(party_panel_close_click)
        # time.sleep(random.uniform(0.1,0.3))

@register_state
class perform_dungeon_elite(state):
    count = 2

    def execute(self):
        perform_dungeons(elite=True, count=self.count)

@register_state
class perform_dungeon_normal(state):
    count = 3

    def execute(self):
        perform_dungeons(elite=False, count=self.count)

@register_state
class perform_zhuagui(state):
    rounds = 5

    def execute(self):
        helper_actions.perform_zhuagui(rounds=self.rounds)

@register_state
class perform_wenqu(state):

    def execute(self):
        x, y, x1, y1 = (70,95,315,460)
        go_to_quest(wenqu_jianshang_path,mask_path=mask_path_, threshold=0.85)

        for window in window_capture_areas_:
            topx, topy, _, _ = window
            start_x = topx + x
            start_y = topy + y
            end_x = topx + x1
            end_y = topy + y1
            complete_counter = 0
            while complete_counter < 5:
                result, val = im.find_icon_on_screen(wenqu_like_path, screen_area=window)
                if result:
                    random_click_mouse(result)
                    time.sleep(random.uniform(2.0, 3.0))
                    complete_counter +=1
                else:
                    random_start_y = random.uniform(end_y + 20,(start_y-end_y)/2 + end_y)
                    random_end_y   = random.uniform(start_y + 20, (start_y-end_y)/2 + end_y)
                    logger.info(f"Dragging from {random_start_y:.1f} to {random_end_y:.1f}")
                    drag_mouse_vertically((start_x, random_start_y, end_x, random_end_y))
                    time.sleep(random.uniform(1.0, 2.0))

        results, vals = im.find_icon_each_window(wenqu_close_path)
        for click, val in zip(results, vals):
            logger.info(f"Found wenqu_close, location {click} found value: {val}")
            random_click_mouse(click)
        time.sleep(3)

@register_state
class perform_qiyuan(state):

    def execute(self):
        ROUND_PAT = re.compile(r"[（(【\[]\s*\d+\s*/\s*\d+\s*[】\])）\]]|\b\d+\s*/\s*\d+\b")
        CN_SPACE_PAT = re.compile(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])")
        PUNCT_SPACE_PAT = re.compile(r"[\s：:，,。．.!！?？;；、'\"“”‘’()（）【】\[\]《》<>·…-]+")

        def load_qiyuan_table(path):
            if not os.path.exists(path):
                return {"questions": {}}
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

        def normalize_question_for_match(text):
            t = (text or "").strip().lower()
            t = CN_SPACE_PAT.sub("", t)
            t = PUNCT_SPACE_PAT.sub("", t)
            return t

        def resolve_similar_question_key(question, qmap, min_ratio=0.86):
            if question in qmap:
                return question

            qn = normalize_question_for_match(question)
            if not qn:
                return None

            best_ratio_key = None
            best_ratio = 0.0
            best_overlap_key = None
            best_overlap = 0

            for key in qmap.keys():
                kn = normalize_question_for_match(key)
                if not kn:
                    continue
                if kn == qn:
                    return key

                if qn in kn or kn in qn:
                    overlap = min(len(qn), len(kn))
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_overlap_key = key

                ratio = SequenceMatcher(None, qn, kn).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_ratio_key = key

            if best_overlap >= 10:
                return best_overlap_key

            dynamic_ratio = 0.92 if len(qn) < 10 else min_ratio
            if best_ratio >= dynamic_ratio:
                return best_ratio_key
            return None

        def extract_question(ocr_result, min_conf=0.55):
            if not ocr_result or not ocr_result[0]:
                return None

            best = None
            for _box, (text, conf) in ocr_result[0]:
                if not text:
                    continue
                t = text.strip()
                if conf < min_conf:
                    continue

                m = re.search(r"第\s*\d+\s*题\s*[:：]?\s*(.*)", t)
                if not m:
                    continue

                tail = m.group(1).strip()
                tail = ROUND_PAT.sub("", tail)
                tail = re.sub(r"\s+", " ", tail).strip()
                tail = CN_SPACE_PAT.sub("", tail)
                tail = tail.strip(" ：:，,。．. ")

                if not tail:
                    continue

                if best is None or float(conf) > best[0]:
                    best = (float(conf), tail)

            return best[1] if best else None

        def get_image_list(entry):
            rounds = entry.get("rounds", [])
            out = []
            for r in rounds:
                if isinstance(r, list):
                    out.extend(r)
            return out

        def try_click_any(images, screen_area):
            for path in images:
                img_path = os.path.normpath(path)
                if not os.path.exists(img_path):
                    continue
                res, score = im.find_icon_on_screen(img_path, screen_area=screen_area)
                if res:
                    logger.info(f"Qiyuan matched {img_path} with score={score}")
                    random_click_mouse(res)
                    return True
            return False

        ocr = None
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        except Exception as e:
            logger.warning(f"PaddleOCR init failed, qiyuan will fallback to random click only: {e}")

        qiyuan_table = load_qiyuan_table(resource_path("qiyuan_table.json"))
        qiyuan_questions = qiyuan_table.get("questions", {})

        go_to_quest(qiyuan_path,mask_path=mask_path_, threshold=0.85)
        
        qiyuan_completion = [False] * len(window_capture_areas_)
        x,y,x1,y1 = qiyuan_area_
        excluded_areas = [(300,240,330,260), (420,240,450,260), (540,240,570,260)]
        while not all(qiyuan_completion):
            check_progresses,_ = im.find_icon_each_window(qiyuan_complete_check_path, threshold=0.9)

            for i, area in enumerate(check_progresses):
                if area != None:
                    clicked = False
                    window = window_capture_areas_[i]

                    if ocr is not None and qiyuan_questions:
                        wx, wy, ww, wh = window
                        focus_region = (wx + ww // 3, wy, ww - ww // 3, wh)
                        ocr_image = im.capture_region(focus_region)
                        ocr_result = ocr.ocr(ocr_image, cls=True)
                        question = extract_question(ocr_result, min_conf=0.55)

                        if question:
                            matched_question = resolve_similar_question_key(question, qiyuan_questions, min_ratio=0.86)
                            if matched_question:
                                entry = qiyuan_questions.get(matched_question, {})
                                images = get_image_list(entry)
                                clicked = try_click_any(images, screen_area=window)
                            else:
                                logger.info(f"Qiyuan unknown question in window {i}, fallback to random click.")
                        else:
                            logger.info(f"Qiyuan question OCR failed in window {i}, fallback to random click.")

                    if not clicked:
                        ax, ay, _, _ = window
                        random_click_mouse((ax+x, ay+y, ax+x1, ay+y1), excluded_areas=excluded_areas)
                else:
                    qiyuan_completion[i] = True
    
            result, val = im.find_icon_on_screen(use_item_path)
            if result:
                logger.info(f"Found use_item_path, location {result} found value: {val}")
                random_click_mouse(result)
            
            if all(qiyuan_completion):
                break
            
            time.sleep(random.uniform(0.25, 0.4))

        
        qiyuan_quit_clicks, vals= im.find_icon_each_window(qiyuan_quit_path, threshold=0.90,)

        for click, val in zip(qiyuan_quit_clicks,vals):
            logger.info(f"quitting qiyuan at {click} with val: {val}")
            random_click_mouse(click) 

@register_state
class perform_keju(state):

    def execute(self):
        go_to_quest(keju_xiangshi_path,mask_path=mask_path_, threshold=0.85)
        
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

@register_state
class perform_menghuan_lottery(state):

    def execute(self):
        fuli_clicks, vals = im.find_icon_each_window(game_promotion_path, threshold=0.9)
        for click, val in zip(fuli_clicks, vals):
            logger.info(f"fuli at {click} with val: {val}")
            random_click_mouse(click)
        
        open_lottery_clicks, vals = im.find_icon_each_window(open_lottery_path, threshold=0.9)
        for click, val in zip(open_lottery_clicks, vals):
            logger.info(f"open_lottery at {click} with val: {val}")
            random_click_mouse(click)       

        menghuan_lottery_areas, vals = im.find_icon_each_window(menghuan_lottery_path)
        for area, val in zip(menghuan_lottery_areas, vals):
            logger.info(f"menghuan_lottery at {area} with val: {val}")
            scratch_horizontally(area)    


        
