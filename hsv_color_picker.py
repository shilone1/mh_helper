import cv2
import numpy as np
import pyautogui

# Function to get the HSV value at the mouse cursor
def get_hsv_under_cursor(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:  # Triggered when the mouse moves
        hsv_value = hsv_image[y, x]  # Get HSV value at (x, y)
        print(f"HSV at ({x}, {y}): {hsv_value}")

# Take a screenshot using pyautogui
screenshot = pyautogui.screenshot()

# Convert the screenshot to an OpenCV-compatible format
image = np.array(screenshot)
image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

# Convert the image to HSV color space
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Display the image and set the mouse callback
cv2.namedWindow("HSV Viewer")
cv2.setMouseCallback("HSV Viewer", get_hsv_under_cursor)

print("Move the mouse over the image window to see HSV values.")
while True:
    # Show the image
    cv2.imshow("HSV Viewer", image)
    # Exit the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()