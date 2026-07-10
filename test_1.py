import cv2
import pyautogui
import numpy as np
import time
from datetime import datetime
#shimen position 500 185 625 230
# def capture_region(region):
#     """Captures a specific region on the screen."""
#     screenshot = pyautogui.screenshot(region=region)
#     return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

# def has_region_changed(prev_image, curr_image, threshold=0.90):
#     """Compares two images and returns if they are different."""
#     result = cv2.matchTemplate(curr_image, prev_image, cv2.TM_CCOEFF_NORMED)
#     _, max_val, _, _ = cv2.minMaxLoc(result)
#     return max_val < threshold

# def check_task_completion(template_path, region):
#     """Checks if the task completion window is visible."""
#     template = cv2.imread(template_path, 0)
#     screen = capture_region(region)
#     screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
#     result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
#     _, max_val, _, _ = cv2.minMaxLoc(result)
#     return max_val > 0.8  # Adjust threshold as needed

# def main():
#     # Define regions for the five windows (adjust coordinates to match your screen setup)
#     regions = [
#         (0, 0, 300, 300),  # Example region for window 1
#         (300, 0, 300, 300),  # Window 2
#         (600, 0, 300, 300),  # Window 3
#         (900, 0, 300, 300),  # Window 4
#         (1200, 0, 300, 300),  # Window 5
#     ]

#     # Placeholder for reference images
#     prev_images = [capture_region(region) for region in regions]
#     stuck_counters = [0] * 5  # Counter to detect stuck characters
#     max_stuck_iterations = 5  # Threshold to decide if a character is stuck

#     task_template_path = "task_complete_template.png"  # Add your completion popup template here

#     while True:
#         for i, region in enumerate(regions):
#             curr_image = capture_region(region)
#             if has_region_changed(prev_images[i], curr_image):
#                 # Reset counter if there's a change
#                 stuck_counters[i] = 0
#                 prev_images[i] = curr_image
#             else:
#                 # Increment counter if no change
#                 stuck_counters[i] += 1

#             # Check if the character is stuck
#             if stuck_counters[i] > max_stuck_iterations:
#                 print(f"Window {i+1} appears to be stuck! Taking recovery action...")
#                 # Implement recovery actions like clicking or refreshing the window
#                 stuck_counters[i] = 0  # Reset after recovery

#         # Check for task completion in all windows
#         completion_counters = [
#             check_task_completion(task_template_path, region) for region in regions
#         ]
#         if all(completion_counters):
#             print(f"All tasks completed at {datetime.now()}!")
#             break

#         time.sleep(1)  # Adjust loop delay as needed

# if __name__ == "__main__":
#     # main()
#     # Global constants for window positioning adjustments
#     WINDOW_BORDER_ADJUST = 11  # Horizontal border adjustment
#     WINDOW_VERTICAL_ADJUST = 50  # Vertical border/title bar adjustment
#     WINDOW_WIDTH = 653  # Width of each game window
#     WINDOW_HEIGHT = 517  # Height of each game window

#     # Adjust window size to account for borders and title bar
#     ADJUSTED_WINDOW_WIDTH = WINDOW_WIDTH - 2 * WINDOW_BORDER_ADJUST  # Subtract border adjustments
#     ADJUSTED_WINDOW_HEIGHT = WINDOW_HEIGHT - WINDOW_VERTICAL_ADJUST  # Subtract vertical adjustment

#     def get_window_positions(screen_width, screen_height, window_width, window_height):
#         """
#         Define positions for 5 windows in a grid layout, adjusted for borders and padding.
#         """
#         positions = []
#         window_positions = {}

#         # First row - Left to right (3 windows)
#         for col in range(3):
#             x = col * window_width
#             x_adjusted = x - WINDOW_BORDER_ADJUST * (col + 1)  # Apply adjustments for horizontal borders
#             y = 0  # Top of the screen
#             positions.append((x_adjusted, y))
#             window_positions[f"window_{col+1}"] = (x - WINDOW_BORDER_ADJUST * col, y)  # Store logical (unadjusted) position

#         # Second row - Right to left (2 windows)
#         for col in range(2):
#             # Calculate base x position for the second row (starting from the right)
#             x = screen_width - (col + 1) * window_width
#             x_adjusted = x + WINDOW_BORDER_ADJUST * col  # Apply adjustments for horizontal borders
#             # Adjust y-position to be below the first row (adding window height and vertical adjustment)
#             y = screen_height - window_height - WINDOW_VERTICAL_ADJUST  # Adjust for vertical positioning
            
#             # Add the windows to the positions list
#             positions.append((x_adjusted, y))
#             window_positions[f"window_{col+4}"] = (x - WINDOW_BORDER_ADJUST * col, y)  # Store logical (unadjusted) position

#         # Now adjust the fifth window to be centered in the second row
#         # The fifth window should be approximately in the middle, not too far to the left or right
#         # Find the position between the 4th and 5th windows
#         fourth_window_x, fourth_window_y = positions[3]  # Get the coordinates of the fourth window
#         fifth_window_x = fourth_window_x - ADJUSTED_WINDOW_WIDTH - WINDOW_BORDER_ADJUST  # Move left of the fourth window
#         fifth_window_y = fourth_window_y  # Keep the same y-position for the second row

#         positions[4] = (fifth_window_x, fifth_window_y)  # Set the fifth window's position

#         return positions, window_positions


#     # Example usage
#     SCREEN_WIDTH = 1920  # Screen width
#     SCREEN_HEIGHT = 1080  # Screen height

#     # Get window positions with adjustments
#     positions, window_positions = get_window_positions(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT)

#     # Print window capture areas
#     window_capture_areas = []
#     for window, position in window_positions.items():
#         x, y = position
#         window_capture_areas.append((x, y, ADJUSTED_WINDOW_WIDTH, ADJUSTED_WINDOW_HEIGHT))

#     print(window_capture_areas)


a = (1,2)
b = (3,4)
def abc(a,b):
    return *a, *b

c = abc(a,b)

print(type(c))

