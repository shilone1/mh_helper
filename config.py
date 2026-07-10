import numpy as np
from app_paths import resource_path

# Screen and window sizes (adjust as needed)
SCREEN_WIDTH = 1920  # Your screen width
SCREEN_HEIGHT = 1080  # Your screen height
WINDOW_WIDTH = 653  # Width of each game window
WINDOW_HEIGHT = 517  # Height of each game window
WINDOW_FOCUS_WIDTH = 1* WINDOW_WIDTH // 2

a1_path = resource_path("img_templates", "a_1.png")
a2_path = resource_path("img_templates", "a_2.png")
a3_path = resource_path("img_templates", "a_3.png")
a4_path = resource_path("img_templates", "a_4.png")
a5_path = resource_path("img_templates", "a_5.png")
a6_path = resource_path("img_templates", "a_6.png")
a7_path = resource_path("img_templates", "a_7.png")
a8_path = resource_path("img_templates", "a_8.png")
a9_path = resource_path("img_templates", "a_9.png")
a10_path = resource_path("img_templates", "a_10.png")

dungeon_paths_ = [{"template_path": a1_path, "filter_range":None},
                  {"template_path": a2_path, "filter_range":None},
                  {"template_path": a3_path, "filter_range":None},
                  {"template_path": a4_path, "filter_range":None},
                  {"template_path": a5_path, "filter_range":None},
                  {"template_path": a6_path, "filter_range":None},
                  {"template_path": a7_path, "filter_range":None},
                  # {"template_path": a8_path, "filter_range":None},
                  {"template_path": a9_path, "filter_range":None},
                #   {"template_path": a10_path, "filter_range":None},
                 ]

game_promotion_path = resource_path("img_templates", "game_promotion.png")
open_lottery_path = resource_path("img_templates", "open_lottery.png")

activity_panel_path = resource_path("img_templates", "activity_panel.png")
quest_template_path = resource_path("img_templates", "b.png")
mask_path_ = resource_path("img_templates", "triangle_mask.png")
inventory_path = resource_path("img_templates", "inventory.png")
inventory_area_ = (360,165,520,400)

selection_menu_path = resource_path("img_templates", "selection_menu.png")
select_daily_panel_path = resource_path("img_templates", "select_daily_panel.png")
button_relative_area_ = (170, 19, 211, 38)
selection_menu_displace_ = (40,50)
selection_menu_button_ = (125,20)

shimen_accept_path = resource_path("img_templates", "shimen_accept.png")
shimen_clicking_area_path = resource_path("img_templates", "shimen_clicking_area.png")
shimen_completed_path = resource_path("img_templates", "shimen_completed.png")
shimen_completed_2_path = resource_path("img_templates", "shimen_completed_2.png")
shimen_completed_click_path = resource_path("img_templates", "shimen_completed_click.png")
quit_shimen_path = resource_path("img_templates", "quit_shimen.png")
use_item_path = resource_path("img_templates", "use_item.png")

baotu_path = resource_path("img_templates", "baotu.png")
baotu_clicks_path = resource_path("img_templates", "baotu_clicks.png")
baotu_item_path = resource_path("img_templates", "baotu_item.png")

auto_battle_path = resource_path("img_templates", "auto_battle.png")
mijing_path = resource_path("img_templates", "mijing.png")
mijing_enter_path = resource_path("img_templates", "mijing_enter.png")
mijing_confirm_path = resource_path("img_templates", "mijing_confirm.png")
mijing_continue_battle_path = resource_path("img_templates", "mijing_continue_battle.png")
mijing_click_path = resource_path("img_templates", "mijing_click.png")
mijing_quit_path = resource_path("img_templates", "mijing_quit.png")

yabiao_path = resource_path("img_templates", "yabiao.png")
yabiao_confirm_path = resource_path("img_templates", "yabiao_confirm.png")
yabiao_complete_2_path = resource_path("img_templates", "yabiao_complete_2.png")

party_panel = (570,95,625,115)
recruit_button_path = resource_path("img_templates", "recruit_button.png")
my_recruit_button_path = resource_path("img_templates", "my_recruit_button.png")
recruit_hall_path = resource_path("img_templates", "recruit_hall.png")
click_to_party_path = resource_path("img_templates", "click_to_party.png")
my_party_recruit_path = resource_path("img_templates", "my_party_recruit.png")
party_accept_path = resource_path("img_templates", "party_accept.png")
party_panel_close_path = resource_path("img_templates", "party_panel_close.png")
party_recruit_close_path = resource_path("img_templates", "party_recruit_close.png")
recruit_hall_close_path = resource_path("img_templates", "recruit_hall_close.png")

in_battle_icon_path = resource_path("img_templates", "in_battle.png")
skip_cinematic_path = resource_path("img_templates", "skip_cinematic.png")
go_battle_path = resource_path("img_templates", "go_battle.png")
dungeon_completed_path = resource_path("img_templates", "dungeon_completed.png")
dungeon_enter_path = resource_path("img_templates", "dungeon_enter.png")
dungeron_click_continue_path = resource_path("img_templates", "dungeron_click_continue.png")
elite_dungeon_panel_path = resource_path("img_templates", "elite_dungeon_panel.png")
elite_dungeon_ready_path = resource_path("img_templates", "elite_dungeon_ready.png")

double_exp_tab_path = resource_path("img_templates", "double_exp_tab.png")
double_exp_acquire_path = resource_path("img_templates", "double_exp_acquire.png")

zhuagui_path = resource_path("img_templates", "zhuagui.png")
zhuagui_proceed_path = resource_path("img_templates", "zhuagui_proceed.png")
zhuagui_continue_path = resource_path("img_templates", "zhuagui_continue.png")

qiyuan_area_= (225, 140, 560, 285)
qiyuan_path = resource_path("img_templates", "qiyuan.png")
qiyuan_complete_check_path = resource_path("img_templates", "qiyuan_complete_check.png")
qiyuan_quit_path = resource_path("img_templates", "qiyuan_quit.png")

expand_bottom_path = resource_path("img_templates", "expand_bottom.png")
home_icon_path = resource_path("img_templates", "home_icon.png")

lottery_enter_path = resource_path("img_templates", "lottery_enter.png")
menghuan_lottery_path = resource_path("img_templates", "menghuan_lottery.png")

auction_sell_path = resource_path("img_templates", "auction_sell.png")
discard_item_path = resource_path("img_templates", "discard_item.png")
discard_confirm_path = resource_path("img_templates", "discard_confirm.png")
sell_path = resource_path("img_templates", "sell.png")
stash_unselected_path = resource_path("img_templates", "stash_unselected.png")
inventory_unselected_path = resource_path("img_templates", "inventory_unselected.png")
inventory_additional_options_path = resource_path("img_templates", "inventory_additional_options.png")
market_to_sell_path = resource_path("img_templates", "market_to_sell.png")
market_launch_path = resource_path("img_templates", "market_launch.png")
confirm_seven_days_path = resource_path("img_templates", "confirm_seven_days.png")
market_sell_confirm_path = resource_path("img_templates", "market_sell_confirm.png")
market_close_path = resource_path("img_templates", "market_close.png")
inventory_arrange_path = resource_path("img_templates", "inventory_arrange.png")

mengjing_path = resource_path("img_templates", "mengjing.png")

defeated_path = resource_path("img_templates", "defeated.png")

menpai_chuangguan_path = resource_path("img_templates", "menpai_chuangguan.png")

wenqu_jianshang_path = resource_path("img_templates", "wenqu_jianshang.png")
wenqu_like_path = resource_path("img_templates", "wenqu_like.png")
wenqu_close_path = resource_path("img_templates", "wenqu_close.png")

keju_xiangshi_path = resource_path("img_templates", "keju_xiangshi.png")

icon_tasks = [
              {"folder": resource_path("img_templates", "items_to_sell"), "key": "sell", "threshold": 0.80},
              {"folder": resource_path("img_templates", "items_to_stash"), "key": "stash", "threshold": 0.80},
             ]

YELLOW_COLOR_RANGE = (np.array([20, 90, 100]), np.array([40, 255, 255]))

window_capture_areas_ = [
(0, 0, 638, 505),    # First window
(638, 0, 638, 505),  # Second window
(1280, 0, 638, 505), # Third window
(1274, 517, 638, 505),  # Fourth window
(632, 517, 638, 505)     # Fifth window
]

right_half_areas_ = []
for left, top, width, height in window_capture_areas_:
    half_width = width // 2
    right_half = (left + half_width, top, half_width, height)
    right_half_areas_.append(right_half)

window_capture_areas_len = len(window_capture_areas_)


NORMAL_DUNGEON_NUM = 2
Mijing_MAX_TRY_OUTS = 3
