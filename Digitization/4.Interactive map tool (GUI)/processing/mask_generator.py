import cv2
import numpy as np

def generate_mask(image, color, tolerance=30):

    lower = np.clip(color - tolerance, 0, 255)
    upper = np.clip(color + tolerance, 0, 255)

    mask = cv2.inRange(image, lower, upper)

    return mask