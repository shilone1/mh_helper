import pygetwindow as gw
from mouse_action import move_mouse_smooth, click_mouse
import win32gui
import win32con
import ctypes

"""
current game window size is 653, 517
"""

# Global constants for window positioning adjustments
WINDOW_BORDER_ADJUST = 11  # Horizontal border adjustment
WINDOW_VERTICAL_ADJUST = 50  # Vertical border/title bar adjustment

def enum_windows_by_title(title_keyword):
    """
    Enumerate all windows containing the given keyword in their title.
    :param title_keyword: The keyword to match in window titles.
    :return: A list of window handles (HWNDs).
    """
    windows = []

    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title_keyword in title:
                windows.append(hwnd)

    win32gui.EnumWindows(callback, None)
    return windows

def relative_to_global(hwnd, x, y):
    """
    Convert relative (x, y) inside a window to global screen coordinates.
    :param hwnd: Handle of the window.
    :param x: Relative X-coordinate.
    :param y: Relative Y-coordinate.
    :return: Tuple of (global_x, global_y) in screen space.
    """
    left, top, _, _ = win32gui.GetWindowRect(hwnd)
    global_x = left + x
    global_y = top + y
    return global_x, global_y

WINDOW_WIDTH = 653  # Width of each game window
WINDOW_HEIGHT = 517
# Adjust window size to account for borders and title bar
ADJUSTED_WINDOW_WIDTH = WINDOW_WIDTH - 2 * WINDOW_BORDER_ADJUST  # Subtract border adjustments
ADJUSTED_WINDOW_HEIGHT = WINDOW_HEIGHT - WINDOW_VERTICAL_ADJUST  # Subtract vertical adjustment

def get_window_positions(screen_width, screen_height, window_width, window_height):
    """
    Define positions for 5 windows in a grid layout, adjusted for borders and padding.
    """
    positions = []
    window_positions = {}

    # First row - Left to right (3 windows)
    for col in range(3):
        x = col * window_width
        x_adjusted = x - WINDOW_BORDER_ADJUST * (col + 1)  # Apply adjustments for horizontal borders
        y = 0  # Top of the screen
        positions.append((x_adjusted, y))
        window_positions[f"window_{col+1}"] = (x - WINDOW_BORDER_ADJUST * col, y)  # Store logical (unadjusted) position

    # Second row - Right to left (2 windows)
    for col in range(2):
        x = screen_width - (col + 1) * window_width
        x_adjusted = x + WINDOW_BORDER_ADJUST * col  # Apply adjustments for horizontal borders
        y = screen_height - window_height - WINDOW_VERTICAL_ADJUST  # Adjust for vertical positioning
        positions.append((x_adjusted, y))
        window_positions[f"window_{col+4}"] = (x - WINDOW_BORDER_ADJUST * col, y)  # Store logical (unadjusted) position

    return positions, window_positions



# deprecated
def get_adjusted_window_size(width, height, style=win32con.WS_OVERLAPPEDWINDOW):
    """
    Adjusts window size to include borders and title bars.
    :param width: Desired client area width.
    :param height: Desired client area height.
    :param style: Window style, default is WS_OVERLAPPEDWINDOW.
    :return: Adjusted width and height that include borders.
    """
    rect = ctypes.wintypes.RECT(0, 0, width, height)
    ctypes.windll.user32.AdjustWindowRect(ctypes.byref(rect), style, False)
    adjusted_width = rect.right - rect.left
    adjusted_height = rect.bottom - rect.top
    print(adjusted_width, adjusted_height)
    return adjusted_width, adjusted_height

# def move_windows_to_positions(window_handles, positions, client_width, client_height):
#     """
#     Move windows to predefined positions while aligning their client areas correctly.
#     :param window_handles: List of window handles (HWNDs).
#     :param positions: List of (x, y) positions for each window.
#     :param client_width: Desired width of the client area.
#     :param client_height: Desired height of the client area.
#     """
#     for hwnd, (x, y) in zip(window_handles, positions):
#         # Adjust window size for borders and title bar
#         adjusted_width, adjusted_height = get_adjusted_window_size(client_width, client_height)

#         # Move the window with adjusted dimensions
#         win32gui.MoveWindow(hwnd, x, y, adjusted_width, adjusted_height, True)
#         print(f"Moved window {hwnd} to ({x}, {y}) with adjusted size ({adjusted_width}, {adjusted_height})")


def move_windows_to_positions(window_handles, positions, window_width, window_height):
    """
    Move windows to predefined positions.
    :param window_handles: List of window handles (HWNDs).
    :param positions: List of (x, y) positions for each window.
    :param window_width: Width to set for each window.
    :param window_height: Height to set for each window.
    """
    for hwnd, (x, y) in zip(window_handles, positions):
        win32gui.MoveWindow(hwnd, x, y, window_width, window_height, True)
        print(f"Moved window {hwnd} to ({x}, {y})")


def set_window_size(window_handles, width, height):
    """
    Resize all windows to the specified width and height.
    :param window_handles: List of window handles (HWNDs).
    :param width: Desired width of the window.
    :param height: Desired height of the window.
    """
    for hwnd in window_handles:
        # Get the current position of the window
        rect = win32gui.GetWindowRect(hwnd)
        left, top = rect[0], rect[1]

        # Move and resize the window
        win32gui.MoveWindow(hwnd, left, top, width, height, True)
        print(f"Resized window {hwnd} to {width}x{height}")

def get_window_size(hwnd):
    """
    Get the size of the window specified by its handle.
    :param hwnd: Handle to the window (HWND).
    :return: (width, height) of the window.
    """
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top
    return width, height

# # Example: Find all windows with the title "梦幻西游手游"
# game_windows = enum_windows_by_title("梦幻西游：时空")


if __name__ == "__main__":

    """
    current game window size is 653, 517
    adjusted size 669 556
    """

    # Screen and window sizes (adjust as needed)
    SCREEN_WIDTH = 1920  # Your screen width
    SCREEN_HEIGHT = 1080  # Your screen height
    WINDOW_WIDTH = 653  # Width of each game window
    WINDOW_HEIGHT = 517  # Height of each game window

    # Get predefined positions
    positions, window_positions = get_window_positions(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT)

    # Find all game windows
    game_windows = enum_windows_by_title("梦幻西游：时空")
    for i in game_windows:
        print(get_window_size(i))

    if len(game_windows) >= 5:
        # Move windows to their respective positions
        move_windows_to_positions(game_windows[:5], positions, WINDOW_WIDTH, WINDOW_HEIGHT)
    else:
        print(f"Found only {len(game_windows)} game windows. Make sure 5 instances are running.")
    
    # print("aaa", window_positions)


