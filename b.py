import cv2
import numpy as np

def preprocess_image(image_path):
    # Load the image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Apply thresholding to make the numbers stand out
    _, thresh = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY_INV)

    return thresh

def load_digit_templates():
    """
    Load pre-saved digit templates (0–9) as grayscale images.
    Returns a dictionary of digit templates.
    """
    templates = {}
    for digit in range(10):
        template_path = f"{digit}.png"
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        templates[str(digit)] = template
    return templates

def recognize_digits(image, templates):
    """
    Recognize digits in the given image using template matching.
    :param image: Thresholded image containing digits
    :param templates: Dictionary of digit templates
    :return: Extracted number as a string
    """
    detected_digits = []
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Sort contours left-to-right for proper digit order
    contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        roi = image[y:y+h, x:x+w]  # Extract the digit region

        # Match the ROI with each digit template
        best_match = None
        best_score = float('inf')
        for digit, template in templates.items():
            resized_template = cv2.resize(template, (w, h))  # Resize template to match ROI size
            score = cv2.matchTemplate(roi, resized_template, cv2.TM_CCOEFF_NORMED).max()
            if score > best_score:
                best_score = score
                best_match = digit

        if best_match is not None:
            detected_digits.append(best_match)

    return ''.join(detected_digits)


# Example Usage
if __name__ == "__main__":
    # Preprocess the input image
    image_path = "/number_image.png"  # Path to your image
    preprocessed_image = preprocess_image(image_path)

    # Load digit templates
    digit_templates = load_digit_templates()

    # Recognize digits
    detected_number = recognize_digits(preprocessed_image, digit_templates)
    print(f"Detected number: {detected_number}")

    # Compare numbers
    if int(detected_number) > 100:
        print("Detected number is greater than 100.")
    else:
        print("Detected number is less than or equal to 100.")

    # template = cv2.imread("number_image.png", cv2.IMREAD_GRAYSCALE)
    # if template is None:
    #     print("Error: Unable to read the template file!")
    # else:
    #     print("Template loaded successfully.")
    
    # cv2.imshow("a",template)
    # cv2.waitKey(0)