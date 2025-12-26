import cv2

def get_blur_score(image):
    return cv2.Laplacian(image, cv2.CV_64F).var()