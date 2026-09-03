from abc import ABC, abstractmethod
import argparse
import json
import os
import random
import sys
import time
import tkinter as tk
from tkinter import messagebox


def ensure_standard_streams():
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    if sys.stdin is None:
        sys.stdin = open(os.devnull, "r")


ensure_standard_streams()

from state import STATE_REGISTRY
from logger import logger
from app_paths import user_data_path
from config import SCREEN_HEIGHT, WINDOW_HEIGHT

CONFIG_FILE = user_data_path("gui_config.json")
UI_WIDTH = 420
UI_X = 50
UI_Y = WINDOW_HEIGHT
UI_BOTTOM_MARGIN = 64
UI_HEIGHT = SCREEN_HEIGHT - UI_Y - UI_BOTTOM_MARGIN
DEFAULT_CONFIG = {
    "elite_dungeons": 2,
    "normal_dungeons": 3,
    "zhuagui_rounds": 5,
    "mijing_max_try_outs": 3,
    "selected_states": []
}


def load_config():
    config = DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return config

    for key in DEFAULT_CONFIG:
        if key in saved_config:
            config[key] = saved_config[key]
    return config


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

class StateMachine:
    def __init__(self, states_list):
        self.states = []
        self.current_state = states_list[0]
        self.load_states(states_list)

    def load_states(self, states_list):
        """Dynamically load state instances using the registry"""
        print("loading the states")
        for state_name in states_list:
            if state_name and state_name in STATE_REGISTRY:
                task = STATE_REGISTRY[state_name](state_name)
                self.states.append((state_name, task))
            else:
                print(f"State '{state_name}' not found. Entering IDLE mode...")

    def run(self):
        """Run the state machine loop"""
        for state in self.states:
            logger.info(f"Current state: {state[0]}")
            state_instance = state[1]

            if state_instance:
                state_instance.execute()
                # print(f"State {self.current_state} finished with result: {result}")

                # # Determine the next state based on result
                # if result == "SUCCESS":
                #     self.current_state = STATE_MACHINE_CONFIG[self.current_state]["on_success"]
                # else:
                #     self.current_state = STATE_MACHINE_CONFIG[self.current_state]["on_failure"]
            # else:
            #     print("Idle state reached. Waiting...")
            #     time.sleep(10)  # Simulate idle time
            #     self.current_state = STATE_MACHINE_CONFIG[self.current_state]["on_success"]

            time.sleep(2)  # Add a small delay before the next execution


def apply_count_config(config):
    import state  # ensure this is imported after tkinter to avoid circular issues
    state.perform_dungeon_elite.count = config["elite_dungeons"]
    state.perform_dungeon_normal.count = config["normal_dungeons"]
    state.perform_zhuagui.rounds = config["zhuagui_rounds"]
    # state.py imports config values with `from config import *`, so update the
    # value in state.py's namespace before perform_mijing executes.
    state.Mijing_MAX_TRY_OUTS = config["mijing_max_try_outs"]


def read_positive_int(entry, label):
    try:
        value = int(entry.get())
    except ValueError:
        raise ValueError(f"{label} must be a number.")
    if value < 0:
        raise ValueError(f"{label} cannot be negative.")
    return value

def launch_selected_states():
    selected_states = [state_name for state_name, var in checkbox_vars.items() if var.get()]
    if not selected_states:
        messagebox.showinfo("Info", "No states selected.")
        return

    # Save dungeon/zhuagui counts
    try:
        config["elite_dungeons"] = read_positive_int(entry_elite, "Elite Dungeons")
        config["normal_dungeons"] = read_positive_int(entry_normal, "Normal Dungeons")
        config["zhuagui_rounds"] = read_positive_int(entry_zhuagui, "Zhuagui Rounds")
        config["mijing_max_try_outs"] = read_positive_int(entry_mijing, "Mijing Max Tries")
    except ValueError as exc:
        messagebox.showerror("Invalid Counts", str(exc))
        return
    config["selected_states"] = selected_states
    save_config(config)

    # Close the selector and run in this console process. Ctrl+C therefore
    # interrupts the active state directly.
    root.destroy()
    apply_count_config(config)
    StateMachine(selected_states).run()


def save_current_ui_state():
    """Remember the UI exactly as left, even when it is closed without running."""
    config["selected_states"] = [
        state_name for state_name, var in checkbox_vars.items() if var.get()
    ]
    config["elite_dungeons"] = entry_elite.get()
    config["normal_dungeons"] = entry_normal.get()
    config["zhuagui_rounds"] = entry_zhuagui.get()
    config["mijing_max_try_outs"] = entry_mijing.get()
    save_config(config)


def on_close():
    save_current_ui_state()
    root.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args, _unknown = parser.parse_known_args()

    # states_list = ["perform_shimen","perform_baotu","perform_mijing","perform_yabiao"]
    # #states_list = ["perform_baotu","perform_mijing","perform_yabiao"]
    # #states_list = ["perform_yabiao","perform_create_party","perform_dungeon_normal"]
    # #states_list = ["perform_zhuagui"]
    # # states_list = ["perform_yabiao"]
    # # states_list = ["perform_menghuan_lottery"]
    # #states_list = ["perform_dungeon_normal"]
    # sm = StateMachine(states_list)
    # sm.run()

    config = load_config()

    root = tk.Tk()
    root.title("Select States to Run")

    root.geometry(f"{UI_WIDTH}x{UI_HEIGHT}+{UI_X}+{UI_Y}")
    root.minsize(UI_WIDTH, UI_HEIGHT)

    tasks_frame = tk.LabelFrame(root, text="Tasks", padx=8, pady=6)
    tasks_frame.pack(fill="x", padx=10, pady=(6, 6))
    tasks_frame.columnconfigure(0, weight=1)
    tasks_frame.columnconfigure(1, weight=1)

    state_names = list(STATE_REGISTRY)
    rows_per_column = (len(state_names) + 1) // 2

    checkbox_vars = {}
    for idx, state_name in enumerate(state_names):
        var = tk.BooleanVar()
        var.set(state_name in config.get("selected_states", []))
        column = idx // rows_per_column
        row = idx % rows_per_column
        tk.Checkbutton(tasks_frame, text=state_name, variable=var).grid(
            row=row, column=column, sticky="w", padx=4, pady=1
        )
        checkbox_vars[state_name] = var

    bottom_frame = tk.Frame(root)
    bottom_frame.pack(fill="x", padx=10, pady=(0, 6))
    bottom_frame.columnconfigure(0, weight=1)
    bottom_frame.columnconfigure(1, minsize=112)

    # Dungeon and Zhuagui custom counts
    counts_frame = tk.LabelFrame(bottom_frame, text="Counts", padx=8, pady=6)
    counts_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    counts_frame.columnconfigure(1, minsize=56)

    tk.Label(counts_frame, text="Elite:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=2)
    entry_elite = tk.Entry(counts_frame, width=6)
    entry_elite.insert(0, str(config["elite_dungeons"]))
    entry_elite.grid(row=0, column=1, sticky="w", pady=2)

    tk.Label(counts_frame, text="Normal:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=2)
    entry_normal = tk.Entry(counts_frame, width=6)
    entry_normal.insert(0, str(config["normal_dungeons"]))
    entry_normal.grid(row=1, column=1, sticky="w", pady=2)

    tk.Label(counts_frame, text="Zhuagui:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=2)
    entry_zhuagui = tk.Entry(counts_frame, width=6)
    entry_zhuagui.insert(0, str(config["zhuagui_rounds"]))
    entry_zhuagui.grid(row=2, column=1, sticky="w", pady=2)

    tk.Label(counts_frame, text="Mijing tries:").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=2)
    entry_mijing = tk.Entry(counts_frame, width=6)
    entry_mijing.insert(0, str(config["mijing_max_try_outs"]))
    entry_mijing.grid(row=3, column=1, sticky="w", pady=2)

    run_button = tk.Button(
        bottom_frame,
        text="Run\nSelected",
        command=launch_selected_states,
        width=12,
        height=4,
    )
    run_button.grid(row=0, column=1, sticky="nsew")

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
