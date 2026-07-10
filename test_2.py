import cv2
import numpy as np
import pyautogui

# Take a screenshot using pyautogui
screenshot = pyautogui.screenshot()

# Convert the screenshot to an OpenCV-compatible format
image = np.array(screenshot)
# Convert RGB to BGR (OpenCV uses BGR by default)
image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

# Convert the image to HSV color space
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Define the range of yellow color in HSV space
lower_yellow = np.array([20, 90, 140])  # Lower bound of yellow
upper_yellow = np.array([40, 255, 255])  # Upper bound of yellow

# Create a mask to isolate yellow areas in the screenshot
yellow_mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)

# Apply the mask to the original image (keeping only yellow regions)
yellow_filtered = cv2.bitwise_and(image, image, mask=yellow_mask)

# Save the yellow filtered screenshot
cv2.imwrite("yellow_filtered_screenshot.png", yellow_filtered)

# Load the template image
template = cv2.imread("ttt.png", cv2.IMREAD_COLOR)

# Convert the template to HSV and apply yellow color filter
template_hsv = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
template_yellow_mask = cv2.inRange(template_hsv, lower_yellow, upper_yellow)
template_filtered = cv2.bitwise_and(template, template, mask=template_yellow_mask)

# Save the yellow filtered template
cv2.imwrite("yellow_filtered_template.png", template_filtered)

# Apply template matching on the processed screen capture (now with black background removed)
result = cv2.matchTemplate(yellow_filtered, template, cv2.TM_CCOEFF_NORMED)

# Define a threshold for a match (you can adjust this value)
threshold = 0.8

# Find all positions where the match score is above the threshold
match_locations = np.where(result > threshold)
match_values = result[match_locations]
print(match_values)

import matplotlib.pyplot as plt

# # For the screenshot
# hue_screenshot = hsv_image[:, :, 0]
# plt.hist(hue_screenshot.ravel(), bins=180, range=[0, 180])
# plt.title("Hue Distribution - Screenshot")
# plt.show()

# # For the template
# template_hsv = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
# hue_template = template_hsv[:, :, 0]
# plt.hist(hue_template.ravel(), bins=180, range=[0, 180])
# plt.title("Hue Distribution - Template")
# plt.show()

# Draw rectangles around all matching regions
for (x, y) in zip(*match_locations):
    top_left = (x, y)[::-1]
    print(top_left)
    bottom_right = (y + template.shape[1], x + template.shape[0])
    cv2.rectangle(yellow_filtered, top_left, bottom_right, (0, 0, 255), 2)

# Show the result with all matches highlighted
cv2.imshow("a", yellow_filtered)
cv2.moveWindow("a", 100, 100)
cv2.waitKey(0)
cv2.destroyAllWindows()
