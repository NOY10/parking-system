import re
import easyocr
from collections import Counter
from config.settings import BHUTAN_REGEX
from anpr.enhancer import enhance_plate

reader = easyocr.Reader(['en'], gpu=False)

def extract_plate(crops):
    results = []
    best_box = None

    for crop in crops:
        for box in crop["boxes"]:
            x1, y1, x2, y2 = box
            best_box = box
            plate_img = crop["img"][y1:y2, x1:x2]

            enhanced = enhance_plate(plate_img)
            if enhanced is None:
                continue

            texts = reader.readtext(enhanced, detail=0)
            for t in texts:
                clean = t.upper().replace(" ", "")
                if re.search(BHUTAN_REGEX, clean):
                    results.append(clean)

    if results:
        return Counter(results).most_common(1)[0][0], best_box
    return None, None
