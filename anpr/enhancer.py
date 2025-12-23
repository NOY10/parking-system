import cv2

def enhance_plate(lp_img):
    if lp_img is None or lp_img.size == 0:
        return None

    h, w = lp_img.shape[:2]
    lp_img = cv2.resize(lp_img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(lp_img, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(3.0, (8, 8))
    return clahe.apply(gray)
