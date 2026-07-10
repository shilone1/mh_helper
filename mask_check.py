import cv2
import numpy as np
import pyautogui

# using_mask = False
# # Load the template and mask
# template = cv2.imread("aaa.png")

# if using_mask:
#     mask = cv2.imread("img_templates/mask_ignore_red_stripe.png", cv2.IMREAD_GRAYSCALE)
# else:
#     mask = None

# # # Convert the mask to a 3-channel image for visualization
# # mask_color = cv2.merge([mask, mask, mask])

# # # Stack the template and mask side by side for comparison
# # stacked = np.hstack((template, mask_color))

# # # Display the stacked images
# # cv2.imshow("Template and Mask", stacked)
# # cv2.waitKey(0)
# # cv2.destroyAllWindows()

# # Check dimensions
# print("Template dimensions:", template.shape[:2])

# if using_mask:
#     print("Mask dimensions:", mask.shape[:2])
#     unique_values = np.unique(mask)
#     print("Mask unique values:", unique_values)

# screenshot = pyautogui.screenshot(region=(500, 185, 125, 45))
# # screenshot.save("aaa.png")
# screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
# result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
# min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
# print("Max match value without mask:", max_val, max_loc)

# if using_mask:
#     result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED,
#                             mask=mask)
#     min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
#     print("Max match value with mask:", max_val, max_loc)

def mark_non_black_pixels(image_path, points):
    """
    Draw red dots on non-black pixels within a triangular region.
    
    :param image_path: Path to the image.
    :param points: List of three points defining the triangle (e.g., [(x1, y1), (x2, y2), (x3, y3)]).
    :return: The modified image with red dots.
    """
    # Load the image
    image = cv2.imread(image_path)
    
    # Create a blank mask with the same dimensions as the image
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    
    # Define the triangle on the mask
    points = np.array([points], dtype=np.int32)
    cv2.fillPoly(mask, points, 255)  # Fill the triangle with white (255)
    
    # Iterate over the image within the mask
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            if mask[y, x] == 255:  # Check if the pixel is inside the triangle
                pixel = image[y, x]
                # If the pixel is not black, mark it with a red dot
                if np.any(pixel != 0):  # Check if the pixel is not black
                    print(f"found non black coordinates at : {x},{y}")
                    image[y, x] = [0, 0, 255]  # Red in BGR (OpenCV uses BGR format)
    
    return image

def turn_non_black_to_white(image_path):
    # Load the image
    image = cv2.imread(image_path)
    
    # Iterate through each pixel in the image
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            # Check if the pixel is non-black (not [0, 0, 0])
            if np.any(image[y, x] != 0):  # If any channel is not 0
                image[y, x] = [255, 255, 255]  # Change to white
    
    return image

# Example usage
image_path = 'examples/black_red_stripe.png'
triangle_points = [(0, 35), (40, 0), (0, 0)]  # Define the vertices of the triangle
modified_image = mark_non_black_pixels(image_path, triangle_points)
save_image = turn_non_black_to_white(image_path)

# Save and display the modified image
# cv2.imwrite('modified_image.jpg', modified_image)  # Save the image with red dots
cv2.imwrite("triangle_mask.png", save_image)
cv2.imshow('Modified Image', modified_image)  # Show the modified image
cv2.waitKey(0)  # Wait until a key is pressed
cv2.destroyAllWindows()  # Close the window