import ctypes
import random
import time
from ctypes import wintypes

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
def drag_mouse_vertically(start_x, start_y, end_y, duration=1.0):
    hold_left_mouse_button(start_x, start_y)

    distance = abs(end_y - start_y)
    steps = max(10, int(distance / 5))
    dy = (end_y - start_y) / steps
    current_y = start_y

    for i in range(steps):
        current_y += dy
        current_y = min(max(int(current_y), 0), SCREEN_HEIGHT)

        random_deviation = random.randint(-5, 5)
        current_y = min(max(current_y + random_deviation, 0), SCREEN_HEIGHT)

        normalized_x, normalized_y = normalize_coordinates(start_x, current_y)

        mi_move = MOUSEINPUT(dx=normalized_x, dy=normalized_y, mouseData=0, 
                             dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, time=0, dwExtraInfo=None)
        send_input(mi_move)

        time.sleep(duration / steps + random.uniform(0.01, 0.05))

    release_left_mouse_button(start_x, current_y)

# Function to perform a random click within a specified area
def random_click_mouse(area, double_click=False, center_bias=True):
    if area is None:
        return False
    
    left, top, right, bottom = area
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2

    if center_bias:
        x = min(max(int(random.gauss(center_x, (right - left) / 6)), left), right)
        y = min(max(int(random.gauss(center_y, (bottom - top) / 6)), top), bottom)
    else:
        x = random.randint(left, right)
        y = random.randint(top, bottom)

    print(f"Clicking at position: ({x}, {y})")

    move_mouse_smooth(x, y, duration=random.uniform(0.2, 0.7))

    time.sleep(random.uniform(0.3, 1.0))
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

# Function to click on an icon found using template matching

# Example usage of dragging
if __name__ == "__main__":
    start_x, start_y = 500, 300
    end_y = 800
    # drag_mouse_vertically(start_x, start_y, end_y, duration=2.0)
    random_click_mouse((100,100,100,100))
