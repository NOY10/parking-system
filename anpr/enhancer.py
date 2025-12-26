import cv2

def enhance_plate(lp_img):
    if lp_img is None or lp_img.size == 0: 
        return None
    
    # 1. Upscale for better OCR accuracy
    height, width = lp_img.shape[:2]
    lp_img = cv2.resize(lp_img, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
    
    # 2. Convert to LAB color space (L = Lightness, A/B = Color)
    lab = cv2.cvtColor(lp_img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # 3. Apply CLAHE only to the Lightness channel
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    
    # 4. Merge back and convert to BGR (color)
    enhanced_lab = cv2.merge((l_enhanced, a, b))
    enhanced_color = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    return enhanced_color