# # import threading
# # from queue import Queue
# # from collections import Counter

# # from ultralytics.models import YOLO
# # from detection.plate_detector import PlateDetector
# # from anpr.ocr import extract_plate
# # from config.settings import *
# # # from database.plate_db import PlateDatabase
# # from state.shared_state import shared_state, lock

# # task_queue = Queue(maxsize=15)


# # import os
# # from datetime import datetime

# # SAVE_ROOT = "DEBUG_rawocr"

# # RAW_DIR = os.path.join(SAVE_ROOT, "raw")
# # OCR_DIR = os.path.join(SAVE_ROOT, "ocr")

# # os.makedirs(RAW_DIR, exist_ok=True)
# # os.makedirs(OCR_DIR, exist_ok=True)

# # ALL_DETECTIONS_DIR = "Debug_all_detections"


# # import cv2
# # import os
# # import time
# # from detection.plate_detector import PlateDetector
# # from anpr.ocr import extract_plate
# # from state.shared_state import shared_state, lock
# # from config.settings import LPD_PATH
# # from anpr.enhancer import enhance_plate
# # from anpr.blur_score import get_blur_score
# # from database.manager import  db_manager;

# # def _worker():
# #     print("🟢 ANPR worker initialized and waiting...")
# #     # plate_detector = PlateDetector(LPD_PATH)

# #     plate_model = YOLO('license_plate_detector.pt')

# #     while True:
# #         # Get (v_id, [crop1, crop2, ... crop8])
# #         task = task_queue.get()
# #         if task is None: break

# #         v_id, crops = task

# #         best_lp_img = None
# #         best_score = -1

# #         # 1: FIND THE BEST IMAGE IN THE BATCH ---
# #         for car_crop in crops:
# #             p_res = plate_model(car_crop, conf=0.40, verbose=False)[0] # Increased conf to 0.40
    
# #             for box in p_res.boxes:
# #                 # Get coordinates
# #                 p_box = box.xyxy.cpu().numpy()[0]
# #                 px1, py1, px2, py2 = map(int, p_box)
                
# #                 # Get YOLO's confidence that this is actually a plate
# #                 detection_conf = float(box.conf) 
                
# #                 lp_img = car_crop[py1:py2, px1:px2]
# #                 if lp_img is None or lp_img.size == 0: continue

# #                 # Calculate sharpness
# #                 sharpness = get_blur_score(lp_img)
                
# #                 # COMBINED SCORE: Combine YOLO's certainty with the image sharpness
# #                 # This prevents picking a very sharp "non-plate" object
# #                 combined_score = sharpness * detection_conf 

# #                 # ---------- SAVE EVERY PROCESSED CROP FOR DEBUG ----------
# #                 # Create a specific folder for this vehicle ID if it doesn't exist
# #                 id_folder = os.path.join(ALL_DETECTIONS_DIR, f"vehicle_{v_id}")
# #                 os.makedirs(id_folder, exist_ok=True)

# #                 # Name includes sharpness and detection confidence for analysis
# #                 timestamp = datetime.now().strftime("%H%M%S_%f")
# #                 filename = f"score_{combined_score:.2f}_conf_{detection_conf:.2f}_sharp_{sharpness:.1f}_{timestamp}.jpg"
# #                 cv2.imwrite(os.path.join(id_folder, filename), lp_img)
# #                 # ---------------------------------------------------------
                
# #                 if combined_score > best_score:
# #                     best_score = combined_score
# #                     best_lp_img = lp_img
        
# #         batch_results = []
       
# #         if best_lp_img is not None:
# #             # Enhance ONLY the best one
# #             # ready_for_ocr = enhance_plate(best_lp_img)
# #             ready_for_ocr = best_lp_img

# #             # Save ONLY the best one
# #             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
# #             raw_path = f"{RAW_DIR}/ID_{v_id}_{timestamp}_raw.jpg"
# #             ocr_path = f"{OCR_DIR}/ID_{v_id}_{timestamp}_ocr.jpg"

# #             cv2.imwrite(raw_path, best_lp_img)
# #             if ready_for_ocr is not None:
# #                 cv2.imwrite(ocr_path, ready_for_ocr)
# #                 # Perform OCR
# #                 extract_plate(ready_for_ocr, batch_results)
        
# #         with lock:
# #             if "anpr_results" not in shared_state:
# #                 shared_state["anpr_results"] = {}

# #             if batch_results:
# #                 # Since we only processed one (the best), 
# #                 # most_common will just be that result.
# #                 most_common = batch_results[0]
# #                 db_manager.update_plate(v_id, most_common)
# #                 shared_state["anpr_results"][v_id] = most_common
# #                 print(f"✅ FINAL PLATE for ID {v_id}: {most_common} (Score: {best_score:.2f})")
# #             else:
# #                 shared_state["anpr_results"][v_id] = "NOT_FOUND"
# #                 print(f"⚠️ No plates could be read for ID {v_id}")
        
# #         task_queue.task_done()


# from collections import Counter
# import datetime
# import os

# import cv2
# from state.shared_state import shared_state, lock
# from database.manager import db_manager
# from anpr.ocr import extract_plate
# from anpr.buffer import task_queue

# OCR_CONF_THRESHOLD = 0.85

# DEBUG_OCR_DIR = "DEBUG_ANPR/ocr"
# os.makedirs(DEBUG_OCR_DIR, exist_ok=True)

# def _worker():
#     print("🟢 ANPR OCR worker started")

#     while True:
#         task = task_queue.get()
#         if task is None:
#             break

#         v_id, plates = task
#         plates = sorted(plates, key=lambda x: x[0], reverse=True)

#         final_text = None
#         ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

#         for idx, (score, plate_img) in enumerate(plates):
#             batch_results = []

#             # ---------- SAVE OCR INPUT ----------
#             ocr_dir = os.path.join(DEBUG_OCR_DIR, f"vehicle_{v_id}")
#             os.makedirs(ocr_dir, exist_ok=True)

#             input_path = os.path.join(
#                 ocr_dir,
#                 f"{ts}_try_{idx}_score_{score:.2f}.jpg"
#             )
#             cv2.imwrite(input_path, plate_img)
#             # -----------------------------------

#             extract_plate(plate_img, batch_results)

#             if batch_results:
#                 final_text = batch_results[0]

#                 # ---------- RENAME SUCCESS ----------
#                 success_path = os.path.join(
#                     ocr_dir,
#                     f"{ts}_SUCCESS_{final_text}.jpg"
#                 )
#                 cv2.imwrite(success_path, plate_img)
#                 # -----------------------------------

#                 break

#         with lock:
#             if "anpr_results" not in shared_state:
#                 shared_state["anpr_results"] = {}

#             if final_text:
#                 shared_state["anpr_results"][v_id] = final_text
#                 db_manager.update_plate(v_id, final_text)
#                 print(f"✅ PLATE CONFIRMED: {v_id} → {final_text}")
#             else:
#                 shared_state["anpr_results"][v_id] = "NOT_FOUND"
#                 print(f"⚠️ OCR FAILED for {v_id}")

#         task_queue.task_done()



# # def _worker():
# #     print("🟢 ANPR OCR worker started")

# #     while True:
# #         task = task_queue.get()
# #         if task is None:
# #             break

# #         v_id, plates = task

# #         # plates = [(score, plate_img), ...]
# #         plates = sorted(plates, key=lambda x: x[0], reverse=True)

# #         final_text = None

# #         for score, plate_img in plates:
# #             batch_results = []
# #             extract_plate(plate_img, batch_results)

# #             if batch_results:
# #                 final_text = batch_results[0]
# #                 break  # ---- EARLY STOP (Issue 4 solved) ----

# #         with lock:
# #             if "anpr_results" not in shared_state:
# #                 shared_state["anpr_results"] = {}

# #             if final_text:
# #                 shared_state["anpr_results"][v_id] = final_text
# #                 db_manager.update_plate(v_id, final_text)
# #                 print(f"✅ PLATE CONFIRMED: {v_id} → {final_text}")
# #             else:
# #                 shared_state["anpr_results"][v_id] = "NOT_FOUND"
# #                 print(f"⚠️ OCR FAILED for {v_id}")

# #         task_queue.task_done()

import threading
import os
import cv2
from datetime import datetime
from state.shared_state import shared_state, lock
from database.manager import db_manager
from anpr.ocr import extract_plate
from anpr.enhancer import enhance_plate 

def anpr_worker_thread(task_queue):
    print("🟢 OCR Worker Thread Active")
    
    while True:
        task = task_queue.get()
        if task is None: break # Shutdown signal

        v_id, plates = task
        final_text = None

        # Loop through candidates (Best score first)
        for idx, (score, plate_img) in enumerate(plates):
            batch_results = []

            plate_img=enhance_plate(plate_img)
            
            try:
                extract_plate(plate_img, batch_results)
            except Exception as e:
                print(f"❌ OCR Error on vehicle {v_id}: {e}")
                continue

            if batch_results:
                final_text = batch_results[0]

                # Create a permanent path for the success image
                save_dir = "static/detected_plates"
                os.makedirs(save_dir, exist_ok=True)
                saved_img_path = os.path.join(save_dir, f"veh_{v_id}_{final_text}.jpg")
                
                # Save the winning image
                cv2.imwrite(saved_img_path, plate_img)
                
                break # Stop at first valid match

        # Update System State
        with lock:
            if "anpr_results" not in shared_state:
                shared_state["anpr_results"] = {}

            if final_text:
                shared_state["anpr_results"][v_id] = final_text
                db_manager.update_plate(v_id, final_text, saved_img_path)
                print(f"🎯 DATABASE UPDATED: {v_id} -> {final_text}")
            else:
                shared_state["anpr_results"][v_id] = "NOT_FOUND"
                db_manager.update_plate(v_id, "NOT_FOUND", "NOT_FOUND")
                print(f"⚠️ OCR FAILED for vehicle {v_id}")

        task_queue.task_done()
