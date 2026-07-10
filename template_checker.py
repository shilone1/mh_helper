import cv2
import numpy as np
import pyautogui
import image_matching as im

# Load the main image and template
mask_path = "img_templates/mask_ignore_red_stripe.png"
image = pyautogui.screenshot()
image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
template = cv2.imread('img_templates/a_6.png')
mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE) if mask_path else None
template_height, template_width = template.shape[:2]

# # Perform template matching
# result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED,mask=mask)
# print(np.isfinite(result).all())  # This should print True if all values are finite
# _,max_val,_,_ = cv2.minMaxLoc(result)
# print("___________---------------------", max_val)

# result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED, mask=mask)
# template_height, template_width = template.shape[:2]

# _,max_val,_,max_loc = cv2.minMaxLoc(result)
# print(max_val)

result = im.find_icon_on_screen("img_templates/a_6.png", mask_path=mask_path)

# Set a threshold to consider it as a match
threshold = 0.8
match_locations = np.where(result >= threshold)

# Find the top-left corner of the best match
top_left = (match_locations[1][0], match_locations[0][0])

# Add padding around the match for context (you can adjust padding as needed)
padding = 50  # You can modify this for more or less surrounding context

# Define the cropped area (including padding)
x1 = max(top_left[0] - padding, 0)
y1 = max(top_left[1] - padding, 0)
x2 = min(top_left[0] + template_width + padding, image.shape[1])
y2 = min(top_left[1] + template_height + padding, image.shape[0])

# Crop the image to the region of interest (ROI)
cropped_image = image[y1:y2, x1:x2]

# Create a mask for non-matching areas
non_match_mask = np.ones_like(cropped_image) * 255  # White mask

# Mark the matching areas with black in the mask
for pt in zip(*match_locations[::-1]):
    # Check if the match is within the cropped region
    if x1 <= pt[0] <= x2 and y1 <= pt[1] <= y2:
        # Mark the matching region with black (as matched area)
        cv2.rectangle(non_match_mask, (pt[0] - x1, pt[1] - y1),
                      (pt[0] - x1 + template_width, pt[1] - y1 + template_height), (0, 0, 0), -1)

# Now, only draw red dots on the non-matching areas in the cropped region
for y in range(0, cropped_image.shape[0], 5):  # Check every 5 pixels (smaller step)
    for x in range(0, cropped_image.shape[1], 5):  # Smaller steps for smaller dots
        if non_match_mask[y, x][0] == 255:  # Non-matching area (white in mask)
            cv2.circle(cropped_image, (x, y), 2, (0, 0, 255), -1)  # Draw smaller red dot

# Display the cropped image with red dots on non-matching areas
cv2.imshow('Cropped Region with Red Dots (Non-matching areas)', cropped_image)

# Optional: Display the original image with the match highlighted
image_with_dots = image.copy()
for pt in zip(*match_locations[::-1]):
    cv2.rectangle(image_with_dots, pt, (pt[0] + template_width, pt[1] + template_height), (0, 255, 0), 2)

# cv2.imshow('Original Image with Matching Regions', image_with_dots)

cv2.waitKey(0)
cv2.destroyAllWindows()
