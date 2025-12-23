import cv2
import numpy as np

def apply_roi(frame, roi_polygon):
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [roi_polygon], 255)
    return cv2.bitwise_and(frame, frame, mask=mask)
