import ctypes
from ctypes import wintypes
import time
import random
from image_matching import find_icon_on_screen
from logger import logger


# Constants for screen dimensions
SCREEN_WIDTH = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_HEIGHT = ctypes.windll.user32.GetSystemMetrics(1)

# Define constants for mouse input
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000

ULONG_PTR = ctypes.POINTER(ctypes.c_ulong)

# Define the MOUSEINPUT and INPUT structures
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("mi", MOUSEINPUT),
    ]

# Function to send mouse input to the system
def send_input(mouse_input):
    input_structure = INPUT(type=INPUT_MOUSE, mi=mouse_input)
    ctypes.windll.user32.SendInput(1, ctypes.byref(input_structure), ctypes.sizeof(INPUT))

# Normalize the coordinates
def normalize_coordinates(x, y):
    normalized_x = int(x * 65535 / SCREEN_WIDTH)
    normalized_y = int(y * 65535 / SCREEN_HEIGHT)
    return normalized_x, normalized_y

# Function to simulate mouse button hold (down)
def hold_left_mouse_button(x, y):
    normalized_x, normalized_y = normalize_coordinates(x, y)
    mi_down = MOUSEINPUT(dx=normalized_x, dy=normalized_y, mouseData=0, 
                         dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE, 
                         time=0, dwExtraInfo=None)
    send_input(mi_down)

# Function to simulate releasing the left mouse button
def release_left_mouse_button(x, y):
    normalized_x, normalized_y = normalize_coordinates(x, y)
    mi_up = MOUSEINPUT(dx=normalized_x, dy=normalized_y, mouseData=0, 
                       dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE, 
                       time=0, dwExtraInfo=None)
    send_input(mi_up)

# Function to move the mouse to a specific position smoothly
def move_mouse_smooth(x, y, duration=0.2):
    current_pos = ctypes.windll.user32.GetCursorPos
    current_x, current_y = ctypes.wintypes.POINT(), ctypes.wintypes.POINT()
    current_pos(ctypes.byref(current_x))
    current_pos(ctypes.byref(current_y))

    start_x, start_y = current_x.x, current_y.y

    distance = ((x - start_x) ** 2 + (y - start_y) ** 2) ** 0.5
    steps = max(10, int(distance / 10))
    dx = (x - start_x) / steps
    dy = (y - start_y) / steps

    for i in range(steps):
        intermediate_x = int(start_x + dx * i)
        intermediate_y = int(start_y + dy * i)

        # Introduce subtle random deviation
        random_deviation = random.uniform(-1, 1)  # Small deviation to make it human-like
        intermediate_y += random_deviation

        # Ensure the y position stays within screen boundaries
        intermediate_y = min(max(intermediate_y, 0), SCREEN_HEIGHT)

        # Normalize coordinates
        normalized_x, normalized_y = normalize_coordinates(intermediate_x, intermediate_y)

        # Move the mouse step by step
        mi_move = MOUSEINPUT(dx=normalized_x, dy=normalized_y, mouseData=0, 
                             dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, time=0, dwExtraInfo=None)
        send_input(mi_move)

        # Adjust sleep dynamically
        time.sleep(duration / steps)

    # Final position to ensure precision
    normalized_x, normalized_y = normalize_coordinates(x, y)
    mi_move = MOUSEINPUT(dx=normalized_x, dy=normalized_y, mouseData=0, 
                         dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, time=0, dwExtraInfo=None)
    send_input(mi_move)

# Function to simulate vertical drag (scrolling an inventory)
def drag_mouse_vertically(area, duration=1.0):
    start_x, start_y, end_x, end_y = area
    start_x = random.uniform(start_x, end_x)
    move_mouse_smooth(start_x, start_y)

    hold_left_mouse_button(start_x, start_y)

    distance = abs(end_y - start_y)
    steps = max(10, int(distance / 5))
    dy = (end_y - start_y) / steps
    current_y = start_y

    for i in range(steps):
        current_y += dy
        current_y = min(max(int(current_y), 0), SCREEN_HEIGHT)

        random_deviation = random.randint(-1, 1)
        current_y = min(max(current_y + random_deviation, 0), SCREEN_HEIGHT)

        normalized_x, normalized_y = normalize_coordinates(start_x, current_y)

        mi_move = MOUSEINPUT(dx=normalized_x, dy=normalized_y, mouseData=0, 
                             dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, time=0, dwExtraInfo=None)
        send_input(mi_move)

        time.sleep(duration / steps)

    release_left_mouse_button(start_x, current_y)

# Function to perform a random click within a specified area
def random_click_mouse(area, double_click=False, center_bias=True, quick_mode=False, excluded_areas=None):
    if area is None:
        return False
    
    # Set default empty list for excluded areas if None is passed
    excluded_areas = excluded_areas or []
    left, top, right, bottom = area
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2

    # Initialize valid position flag + max retries (prevents infinite loop)
    valid_pos = False
    max_retries = 20
    retry_count = 0
    x, y = 0, 0

    # Loop: generate position → check if it's NOT in excluded areas → use it
    while not valid_pos and retry_count < max_retries:
        # ✅ Original position generation logic (unchanged)
        if center_bias:
            # Gaussian/center-biased random (your original formula)
            x = min(max(int(random.gauss(center_x, (right - left) / 6)), left), right)
            y = min(max(int(random.gauss(center_y, (bottom - top) / 6)), top), bottom)
        else:
            # Uniform random across the entire area
            x = random.randint(left, right)
            y = random.randint(top, bottom)

        # ✅ CORE NEW LOGIC: Check if (x,y) is inside ANY excluded area
        pos_in_excluded = False
        for ex_area in excluded_areas:
            ex_left, ex_top, ex_right, ex_bottom = ex_area
            # Check if x is between ex_left/ex_right AND y between ex_top/ex_bottom
            if ex_left <= x <= ex_right and ex_top <= y <= ex_bottom:
                pos_in_excluded = True
                break  # No need to check other excluded areas
        
        # If position is safe (not in excluded areas), use it
        valid_pos = not pos_in_excluded
        retry_count += 1

    # Edge case: all retries failed (all positions in area are excluded) → return False
    if not valid_pos:
        logger.warning(f"Failed to find valid click position: all area is excluded! Area={area}")
        return False

    # ✅ Original click logic (COMPLETELY UNCHANGED)
    logger.info(f"Clicking at position: ({x}, {y})")
    
    if not quick_mode:
        move_mouse_smooth(x, y, duration=random.uniform(0.2, 0.5))
    else:
        move_mouse_smooth(x, y, duration=0.1)

    if not quick_mode:
        time.sleep(random.uniform(1.0, 2.0))
        
    click_mouse()

    if double_click:
        time.sleep(random.uniform(0.05, 0.1))
        click_mouse()

    time.sleep(random.uniform(0.5, 1.0))
    return (x, y)

# Function to simulate a click
def click_mouse():
    mi_down = MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_LEFTDOWN, time=0, dwExtraInfo=None)
    send_input(mi_down)

    time.sleep(0.05)

    mi_up = MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_LEFTUP, time=0, dwExtraInfo=None)
    send_input(mi_up)

def scratch_horizontally(area, base_duration=1.2, row_step=6,
                         completion_check=None, overshoot_chance=0.3):
    """Scratch slightly angled rows, optionally stopping on confirmed completion.

    completion_check is called with no arguments before scratching and after
    each released stroke. It must report a positive game completion signal,
    not merely a failed match against the unscratched coating. Return True
    only when completion is confirmed; exhausting the rows returns False.
    A full pass is the hard stop regardless of the visual check result.
    """
    left, top, right, bottom = map(int, area)
    if right <= left or bottom <= top or row_step <= 0 or base_duration <= 0:
        raise ValueError("Scratch area, row_step and duration must be positive")
    if not 0 <= overshoot_chance <= 1:
        raise ValueError("overshoot_chance must be between 0 and 1")

    rows = list(range(top, bottom, row_step))
    ordered_rows = []
    while rows:
        cluster_size = random.randint(1, 4)
        cluster, rows = rows[:cluster_size], rows[cluster_size:]
        if random.random() < 0.5:
            cluster.reverse()
        insert_pos = random.randint(0, len(ordered_rows))
        ordered_rows[insert_pos:insert_pos] = cluster

    def clamp_point(x, y):
        return (min(max(int(x), 0), SCREEN_WIDTH - 1),
                min(max(int(y), 0), SCREEN_HEIGHT - 1))

    if completion_check is not None and completion_check():
        return True

    reverse = random.random() < 0.5
    for y in ordered_rows:
        row_duration = base_duration * random.uniform(0.7, 1.5) / len(ordered_rows)
        # Extend beyond either edge independently on some strokes.
        start_x = left - random.randint(5, 15) if random.random() < overshoot_chance else left
        end_x = right + random.randint(5, 15) if random.random() < overshoot_chance else right - 1
        # Keep the slope small relative to row spacing to avoid large gaps.
        tilt = random.uniform(-row_step / 2, row_step / 2)
        center_y = y + random.uniform(-1, 1)
        start_x, start_y = clamp_point(start_x, center_y - tilt / 2)
        end_x, end_y = clamp_point(end_x, center_y + tilt / 2)
        if reverse:
            start_x, end_x = end_x, start_x
            start_y, end_y = end_y, start_y
        reverse = not reverse

        move_mouse_smooth(start_x, start_y)
        current_x, current_y = start_x, start_y
        try:
            hold_left_mouse_button(start_x, start_y)
            steps = max(5, int(abs(end_x - start_x) / 10))
            for i in range(1, steps + 1):
                fraction = i / steps
                jitter = random.uniform(-1, 1) if i < steps else 0
                current_x, current_y = clamp_point(
                    start_x + (end_x - start_x) * fraction,
                    start_y + (end_y - start_y) * fraction + jitter)
                norm_x, norm_y = normalize_coordinates(current_x, current_y)
                move = MOUSEINPUT(dx=norm_x, dy=norm_y, mouseData=0,
                                 dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
                                 time=0, dwExtraInfo=None)
                send_input(move)
                time.sleep(row_duration / steps)
        finally:
            release_left_mouse_button(current_x, current_y)
        time.sleep(random.uniform(0.01, 0.05))
        if completion_check is not None and completion_check():
            logger.info("Lottery completion confirmed; stopping scratch strokes")
            return True

    return False

# Function to click on an icon found using template matching

# Example usage of dragging
# if __name__ == "__main__":
    # start_x, start_y = 500, 300
    # end_y = 800
    # inventory_area = (360,400,520,165)
    # # drag_mouse_vertically(start_x, start_y, end_y, duration=2.0)
    # # random_click_mouse((100,100,100,100))
    # drag_mouse_vertically(inventory_area)

