from abc import ABC, abstractmethod
import argparse
import importlib
import json
import os
import random
import subprocess
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
import mouse_sync
from app_paths import app_dir, user_data_path
from config import SCREEN_HEIGHT, SCREEN_WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH
from get_windows import enum_windows_by_title, get_window_positions, move_windows_to_positions

CONFIG_FILE = user_data_path("gui_config.json")
STATUS_FILE = user_data_path("state_status.txt")
STATUS_ENV_VAR = "MH_HELPER_STATUS_FILE"
GAME_WINDOW_TITLE = "\u68a6\u5e7b\u897f\u6e38\uff1a\u65f6\u7a7a"
UI_WIDTH = 420
UI_X = 50
UI_Y = WINDOW_HEIGHT
UI_BOTTOM_MARGIN = 64
UI_HEIGHT = SCREEN_HEIGHT - UI_Y - UI_BOTTOM_MARGIN
DEFAULT_CONFIG = {
    "elite_dungeons": 2,
    "normal_dungeons": 3,
    "zhuagui_rounds": 5,
    "selected_states": []
}
active_process = None
active_process_name = None
active_status_file = None
STATE_NAME_MIGRATIONS = {
    "perform_zhuagui_normal": "perform_zhuagui",
    "perform_zhuagui_long": "perform_zhuagui",
}

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
            write_status(state[0])
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
        write_status("Finished")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    else:
        config = DEFAULT_CONFIG.copy()

    selected_states = []
    for state_name in config.get("selected_states", []):
        migrated_name = STATE_NAME_MIGRATIONS.get(state_name, state_name)
        if migrated_name not in selected_states:
            selected_states.append(migrated_name)
    config["selected_states"] = selected_states

    for key, value in DEFAULT_CONFIG.items():
        config.setdefault(key, value)
    return config

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def write_status(message):
    status_file = os.environ.get(STATUS_ENV_VAR)
    if not status_file:
        return
    with open(status_file, "w", encoding="utf-8") as f:
        f.write(message)


def apply_count_config(config):
    import state  # ensure this is imported after tkinter to avoid circular issues
    state.perform_dungeon_elite.count = config["elite_dungeons"]
    state.perform_dungeon_normal.count = config["normal_dungeons"]
    state.perform_zhuagui.rounds = config["zhuagui_rounds"]


def run_selected_from_config():
    config = load_config()
    selected_states = config.get("selected_states", [])
    if not selected_states:
        print("No states selected.")
        return
    apply_count_config(config)
    sm = StateMachine(selected_states)
    sm.run()


def run_arrange_inventory():
    importlib.import_module("test_3")


def arrange_game_windows():
    positions, _ = get_window_positions(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT)
    game_windows = enum_windows_by_title(GAME_WINDOW_TITLE)

    if len(game_windows) < 5:
        messagebox.showwarning(
            "Arrange Windows",
            f"Found only {len(game_windows)} game windows. Make sure 5 instances are running.",
        )
        return

    move_windows_to_positions(game_windows[:5], positions, WINDOW_WIDTH, WINDOW_HEIGHT)


def launch_arrange_windows():
    arrange_game_windows()


def launch_mouse_sync():
    if getattr(sys, "frozen", False):
        launch_process([sys.executable, "--mouse-sync"], "Mouse Sync")
    else:
        launch_python_script("mouse_sync.py", "Mouse Sync")


def launch_arrange_inventory():
    if getattr(sys, "frozen", False):
        launch_process([sys.executable, "--arrange-inventory"], "Arrange Inventory")
    else:
        launch_python_script("test_3.py", "Arrange Inventory")


def command_for_script(script_name):
    return [sys.executable, os.path.join(os.path.dirname(__file__), script_name)]


def launch_python_script(script_name, display_name):
    launch_process(command_for_script(script_name), display_name)


def launch_process(command, display_name, status_file=None):
    global active_process, active_process_name, active_status_file

    if active_process is not None and active_process.poll() is None:
        messagebox.showinfo("Info", f"{active_process_name} is already running.")
        return

    env = os.environ.copy()
    if status_file:
        try:
            os.remove(status_file)
        except FileNotFoundError:
            pass
        env[STATUS_ENV_VAR] = status_file

    popen_kwargs = {
        "cwd": app_dir(),
        "env": env,
    }
    if getattr(sys, "frozen", False):
        popen_kwargs.update(
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    active_process = subprocess.Popen(command, **popen_kwargs)
    active_process_name = display_name
    active_status_file = status_file
    set_running_state(display_name)
    root.after(1000, poll_active_process)


def set_running_state(display_name):
    status_var.set(f"Running: {display_name}")
    run_button.config(text="Stop\nTask", command=stop_active_process, state="normal")


def set_idle_state(message="Idle"):
    status_var.set(message)
    run_button.config(text="Run\nSelected", command=launch_selected_states, state="normal")


def poll_active_process():
    global active_process, active_process_name, active_status_file

    if active_process is None:
        return

    update_status_from_file()

    if active_process.poll() is None:
        root.after(1000, poll_active_process)
        return

    finished_name = active_process_name
    active_process = None
    active_process_name = None
    active_status_file = None
    set_idle_state(f"Finished: {finished_name}")


def update_status_from_file():
    if not active_status_file or not os.path.exists(active_status_file):
        return
    with open(active_status_file, "r", encoding="utf-8") as f:
        status = f.read().strip()
    if status:
        status_var.set(f"Running: {status}")


def stop_active_process():
    global active_process, active_process_name, active_status_file

    if active_process is None or active_process.poll() is not None:
        set_idle_state()
        return

    stopped_name = active_process_name
    active_process.terminate()
    try:
        active_process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        active_process.kill()
    active_process = None
    active_process_name = None
    active_status_file = None
    set_idle_state(f"Stopped: {stopped_name}")


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
    except ValueError as exc:
        messagebox.showerror("Invalid Counts", str(exc))
        return
    config["selected_states"] = selected_states
    save_config(config)

    if getattr(sys, "frozen", False):
        command = [sys.executable, "--run-selected"]
    else:
        command = [sys.executable, __file__, "--run-selected"]
    launch_process(command, "Selected States", status_file=STATUS_FILE)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-selected", action="store_true")
    parser.add_argument("--mouse-sync", action="store_true")
    parser.add_argument("--arrange-inventory", action="store_true")
    args, _unknown = parser.parse_known_args()
    if args.run_selected:
        run_selected_from_config()
        raise SystemExit
    if args.mouse_sync:
        mouse_sync.main()
        raise SystemExit
    if args.arrange_inventory:
        run_arrange_inventory()
        raise SystemExit

    # states_list = ["perform_shimen","perform_baotu","perform_mijing","perform_yabiao"]
    # #states_list = ["perform_baotu","perform_mijing","perform_yabiao"]
    # #states_list = ["perform_yabiao","perform_create_party","perform_dungeon_normal"]
    # #states_list = ["perform_zhuagui"]
    # # states_list = ["perform_yabiao"]
    # # states_list = ["perform_menghuan_lottery"]
    # #states_list = ["perform_dungeon_normal"]
    # sm = StateMachine(states_list)
    # sm.run()

# Load remembered config
    config = load_config()

    root = tk.Tk()
    root.title("Select States to Run")

    root.geometry(f"{UI_WIDTH}x{UI_HEIGHT}+{UI_X}+{UI_Y}")
    root.minsize(UI_WIDTH, UI_HEIGHT)

    helper_frame = tk.LabelFrame(root, text="Client Tools", padx=8, pady=6)
    helper_frame.pack(fill="x", padx=10, pady=(6, 6))
    helper_frame.columnconfigure(0, weight=1)
    helper_frame.columnconfigure(1, weight=1)

    tk.Button(helper_frame, text="Arrange Windows", command=launch_arrange_windows).grid(
        row=0, column=0, sticky="ew", padx=(0, 4)
    )
    tk.Button(helper_frame, text="Mouse Sync", command=launch_mouse_sync).grid(
        row=0, column=1, sticky="ew", padx=(4, 0)
    )
    tk.Button(helper_frame, text="Arrange Inventory", command=launch_arrange_inventory).grid(
        row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0)
    )

    tasks_frame = tk.LabelFrame(root, text="Tasks", padx=8, pady=6)
    tasks_frame.pack(fill="x", padx=10, pady=(0, 6))
    tasks_frame.columnconfigure(0, weight=1)
    tasks_frame.columnconfigure(1, weight=1)

    state_names = list(STATE_REGISTRY)
    rows_per_column = (len(state_names) + 1) // 2

    checkbox_vars = {}
    for idx, state_name in enumerate(state_names):
        var = tk.BooleanVar()
        var.set(state_name in config.get("selected_states", []))  # restore last state
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

    run_button = tk.Button(
        bottom_frame,
        text="Run\nSelected",
        command=launch_selected_states,
        width=12,
        height=4,
    )
    run_button.grid(row=0, column=1, sticky="nsew")

    action_frame = tk.Frame(root)
    action_frame.pack(fill="x", padx=10, pady=(0, 6))

    status_var = tk.StringVar(value="Idle")
    tk.Label(action_frame, textvariable=status_var, anchor="w").pack(fill="x")

    def on_close():
        stop_active_process()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
