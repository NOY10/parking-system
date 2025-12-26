import os
import re
import cv2
from datetime import datetime
from config.settings import BHUTAN_REGEX
from paddlex import create_model
import re

# Initialize the lightweight recognition-only model
# This is ideal for already-cropped plates on a CPU
# rec_model = create_model(model_name="PP-OCRv5_mobile_rec")

rec_model = create_model(model_name="PP-OCRv5_server_rec")

# pipeline = create_pipeline(
#     pipeline="OCR",
#     model_name="PP-OCRv5_mobile" # Uses the ~16MB mobile model instead of the 80MB+ server model
# )


def extract_plate(ready_for_ocr, batch_results):
    if ready_for_ocr is None: 
        return

    # --- DEBUG VIEW START ---
    # Create a debug folder if it doesn't exist
    os.makedirs("Debug_ocr", exist_ok=True)
    # Use a timestamp to avoid overwriting files
    from datetime import datetime
    ts = datetime.now().strftime("%H%M%S_%f")
    cv2.imwrite(f"debug_ocr/input_{ts}.jpg", ready_for_ocr)
    # --- DEBUG VIEW END ---

    # 1. Run inference (Returns a generator)
    output_generator = rec_model.predict(ready_for_ocr)

    # 2. Iterate through the generator to get results
    for res in output_generator:
        # PaddleX result objects have a .json attribute
        data = res.json['res']
        
        # In 'rec' (recognition only) models, keys are 'rec_text' and 'rec_score'
        if 'rec_text' in data:
            text = data['rec_text']
            score = data['rec_score']
            
            # Standardize text for Bhutanese Regex
            clean_text = text.upper().replace(" ", "").replace("-", "").strip()

            print(f"🔍 [RAW OCR]: {clean_text} (Score: {score:.2f})")

            # 3. Check against Regex
            if re.search(BHUTAN_REGEX, clean_text):
                batch_results.append(clean_text)
                print(f"🎯 [MATCHED]: {clean_text}")
# # Initialize the full OCR pipeline (Detection + Recognition)
# # This uses PP-OCRv5 by default in the latest versions
# pipeline = create_pipeline(
#     pipeline="OCR",
#     model_name="PP-OCRv5_mobile" # Uses the ~16MB mobile model instead of the 80MB+ server model
# )

# def extract_plate(ready_for_ocr, batch_results):
#     if ready_for_ocr is None:
#         return

#     # Run inference
#     # Note: PaddleX pipelines handle numpy arrays (cv2 images) directly
#     output = pipeline.predict(ready_for_ocr)

#     for res in output:
#         # res.json contains the 'rec_texts' (the actual string)
#         # and 'rec_scores' (confidence)
#         data = res.json['res']
        
#         if 'rec_texts' in data:
#             for text, score in zip(data['rec_texts'], data['rec_scores']):
#                 clean_text = text.upper().replace(" ", "").replace("-", "").strip()
                
#                 # Check against your Bhutan Regex
#                 if re.search(BHUTAN_REGEX, clean_text):
#                     batch_results.append(clean_text)
#                     print(f"🎯 [PP-OCRv5] Detected: {clean_text} (Score: {score:.2f})")