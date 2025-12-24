import re
import easyocr
from collections import Counter
from config.settings import BHUTAN_REGEX
from anpr.enhancer import enhance_plate

reader = easyocr.Reader(['en'], gpu=False)
def extract_plate(inputs):
    results = []
    best_box = None

    for item in inputs:
        plate_img = item["plate"]
        box = item["box"]

        enhanced = enhance_plate(plate_img)
        if enhanced is None:
            continue

        texts = reader.readtext(enhanced, detail=0)
        for t in texts:
            clean = t.upper().replace(" ", "")
            if re.search(BHUTAN_REGEX, clean):
                results.append(clean)
                best_box = box

    if results:
        return Counter(results).most_common(1)[0][0], best_box

    return None, None
