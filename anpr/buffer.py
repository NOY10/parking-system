# import cv2
# import os
# from anpr.worker import task_queue
# from config.settings import BUFFER_SIZE
# from datetime import datetime

# car_buffer = {}
# processed = set()
# processed_ids = set()
# final_results = {}

# # Ensure a debug folder exists
# DEBUG_DIR = "Debug_img"
# os.makedirs(DEBUG_DIR, exist_ok=True)

# def update_anpr(v_id, frame, box):
#     x1, y1, x2, y2 = map(int, box)
    
#     if v_id not in final_results and v_id not in processed_ids:
#         if v_id not in car_buffer: car_buffer[v_id] = []
        
#         if len(car_buffer[v_id]) < BUFFER_SIZE:
#             # Create the crop
#             crop = frame[y1:y2, x1:x2].copy()
#             car_buffer[v_id].append(crop)

#             # ---------- SAVE FOR DEBUG ----------
#             # Format: debug_crops/ID_1_20251226_111530_123456_crop_0.jpg
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
#             crop_index = len(car_buffer[v_id]) - 1
#             filename = f"ID_{v_id}_{timestamp}_crop_{crop_index}.jpg"
#             save_path = os.path.join(DEBUG_DIR, filename)
            
#             cv2.imwrite(save_path, crop)
#             # ------------------------------------

#         elif len(car_buffer[v_id]) == BUFFER_SIZE:
#             if not task_queue.full():
#                 task_queue.put((v_id, car_buffer[v_id]))
#                 processed_ids.add(v_id)
#             car_buffer.pop(v_id, None)



# import cv2
# import os
# import time
# from collections import defaultdict
# from datetime import datetime
# from queue import Queue

# from anpr.blur_score import get_blur_score
# from detection.plate_detector import PlateDetector
# from config.settings import BUFFER_SIZE, LPD_PATH

# # ================== INIT ==================
# plate_detector = PlateDetector(LPD_PATH)

# car_buffer = defaultdict(list)     # v_id -> [(score, plate_img)]
# processed_ids = set()
# locked_ids = set()
# no_plate_ids = set()

# task_queue = Queue(maxsize=20)

# first_seen_time = {}

# # ================== TUNING ==================
# MIN_SHARPNESS = 40        # LOWERED (important)
# MIN_PLATE_WIDTH = 60      # LOWERED
# BEST_SCORE_THRESHOLD = 80 # LOWERED
# MAX_SCAN_TIME_SEC = 30
# MAX_PLATES_PER_VEHICLE = BUFFER_SIZE

# # ================== DEBUG DIRS ==================
# DEBUG_ROOT = "DEBUG_ANPR"
# VEHICLE_DIR = os.path.join(DEBUG_ROOT, "vehicle")
# PLATE_DIR = os.path.join(DEBUG_ROOT, "plates")

# os.makedirs(VEHICLE_DIR, exist_ok=True)
# os.makedirs(PLATE_DIR, exist_ok=True)

# # =================================================
# def update_anpr(v_id, frame, box):
#     # ---------- HARD STOP ----------
#     if v_id in processed_ids or v_id in locked_ids or v_id in no_plate_ids:
#         return

#     now = time.time()

#     # ---------- FIRST SEEN ----------
#     if v_id not in first_seen_time:
#         first_seen_time[v_id] = now
#         print(f"🚗 Vehicle {v_id} entered ANPR scan")

#     elapsed = now - first_seen_time[v_id]

#     # ---------- TIMEOUT ----------
#     if elapsed > MAX_SCAN_TIME_SEC:
#         print(f"⏱️ TIMEOUT: No clear plate for vehicle {v_id}")
#         no_plate_ids.add(v_id)
#         car_buffer.pop(v_id, None)
#         first_seen_time.pop(v_id, None)
#         return

#     # ---------- VEHICLE CROP ----------
#     x1, y1, x2, y2 = map(int, box)
#     vehicle_crop = frame[y1:y2, x1:x2]

#     if vehicle_crop.size == 0:
#         return

#     ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

#     # ---------- SAVE VEHICLE (EVERY FRAME – DEBUG) ----------
#     veh_dir = os.path.join(VEHICLE_DIR, f"vehicle_{v_id}")
#     os.makedirs(veh_dir, exist_ok=True)
#     cv2.imwrite(
#         os.path.join(veh_dir, f"{ts}_vehicle.jpg"),
#         vehicle_crop
#     )

#     # ---------- PLATE DETECTION ----------
#     plate_boxes = plate_detector.detect(vehicle_crop, conf=0.2)

#     print(
#         f"🔍 v_id={v_id} "
#         f"time={elapsed:.2f}s "
#         f"plates_detected={len(plate_boxes)}"
#     )

#     if not plate_boxes:
#         return  # keep scanning

#     # ---------- PROCESS EACH PLATE ----------
#     for px1, py1, px2, py2, det_conf in plate_boxes:
#         plate_crop = vehicle_crop[py1:py2, px1:px2]
#         if plate_crop.size == 0:
#             continue

#         h, w = plate_crop.shape[:2]
#         if w < MIN_PLATE_WIDTH:
#             print(f"⚠️ Plate too small ({w}px)")
#             continue

#         sharpness = get_blur_score(plate_crop)
#         if sharpness < MIN_SHARPNESS:
#             print(f"⚠️ Blurry plate (sharp={sharpness:.1f})")
#             continue

#         score = sharpness * det_conf

#         print(
#             f"✅ Plate candidate | sharp={sharpness:.1f} "
#             f"conf={det_conf:.2f} score={score:.1f}"
#         )

#         # ---------- SAVE PLATE DEBUG ----------
#         plate_dir = os.path.join(PLATE_DIR, f"vehicle_{v_id}")
#         os.makedirs(plate_dir, exist_ok=True)

#         fname = (
#             f"{ts}_score_{score:.1f}"
#             f"_sharp_{sharpness:.1f}"
#             f"_conf_{det_conf:.2f}.jpg"
#         )
#         cv2.imwrite(os.path.join(plate_dir, fname), plate_crop)

#         # ---------- BUFFER ----------
#         car_buffer[v_id].append((score, plate_crop))
#         car_buffer[v_id] = sorted(
#             car_buffer[v_id],
#             key=lambda x: x[0],
#             reverse=True
#         )[:MAX_PLATES_PER_VEHICLE]

#         # ---------- EARLY STOP ----------
#         if score >= BEST_SCORE_THRESHOLD:
#             print(f"🏁 LOCKED plate for vehicle {v_id}")

#             locked_ids.add(v_id)

#             if not task_queue.full():
#                 task_queue.put((v_id, car_buffer[v_id]))
#                 processed_ids.add(v_id)

#             # cleanup
#             car_buffer.pop(v_id, None)
#             first_seen_time.pop(v_id, None)
#             return


import cv2
import os
import time
from collections import defaultdict
from datetime import datetime
from queue import Queue

from anpr.blur_score import get_blur_score
from detection.plate_detector import PlateDetector
from config.settings import BUFFER_SIZE, LPD_PATH

# ================== INIT ==================
plate_detector = PlateDetector(LPD_PATH)


car_buffer = defaultdict(list)     
processed_ids = set()
locked_ids = set()
no_plate_ids = set()

# Shared queue for the OCR worker
task_queue = Queue(maxsize=20)

first_seen_time = {}

# ================== TUNING ==================
MIN_SHARPNESS = 40        
MIN_PLATE_WIDTH = 60      
BEST_SCORE_THRESHOLD = 85 
MAX_SCAN_TIME_SEC = 120
MAX_PLATES_PER_VEHICLE = BUFFER_SIZE

# ================== DEBUG DIRS ==================
DEBUG_ROOT = "DEBUG_ANPR"
VEHICLE_DIR = os.path.join(DEBUG_ROOT, "vehicle")
BATCH_DIR = os.path.join(DEBUG_ROOT, "ocr_batches")

os.makedirs(VEHICLE_DIR, exist_ok=True)
os.makedirs(BATCH_DIR, exist_ok=True)

# ================== HELPERS ==================
def save_ocr_batch(v_id, plates):
    """
    Saves the entire batch of best plates that are being sent to OCR.
    This allows you to see exactly what the worker is processing.
    """
    batch_path = os.path.join(BATCH_DIR, f"vehicle_{v_id}")
    os.makedirs(batch_path, exist_ok=True)
    
    for i, (score, img) in enumerate(plates):
        # Format: Rank_0 is the highest score
        fname = f"rank_{i}_score_{score:.1f}.jpg"
        cv2.imwrite(os.path.join(batch_path, fname), img)

# ================== CORE LOGIC ==================
def update_anpr(v_id, frame, box):
    # ---------- HARD STOP ----------
    if v_id in processed_ids or v_id in locked_ids or v_id in no_plate_ids:
        return

    now = time.time()

    # ---------- FIRST SEEN ----------
    if v_id not in first_seen_time:
        first_seen_time[v_id] = now
        print(f"🚗 Vehicle {v_id} entered ANPR scan")

    elapsed = now - first_seen_time[v_id]

    # ---------- TIMEOUT (BEST EFFORT) ----------
    # If car has been in view too long without a "perfect" score, 
    # send whatever we have to OCR anyway.
    if elapsed > MAX_SCAN_TIME_SEC:
        if v_id in car_buffer and car_buffer[v_id]:
            print(f"⏱️ TIMEOUT: Sending best available plates for vehicle {v_id}")
            
            # Save the images being sent
            save_ocr_batch(v_id, car_buffer[v_id])
            
            # Push to OCR
            if not task_queue.full():
                task_queue.put((v_id, car_buffer[v_id]))
                processed_ids.add(v_id)
        else:
            print(f"⏱️ TIMEOUT: No plates ever found for vehicle {v_id}")
            no_plate_ids.add(v_id)
            
        car_buffer.pop(v_id, None)
        first_seen_time.pop(v_id, None)
        return

    # ---------- VEHICLE CROP ----------
    x1, y1, x2, y2 = map(int, box)
    # Ensure crop is within frame boundaries
    vehicle_crop = frame[max(0, y1):y2, max(0, x1):x2]

    if vehicle_crop.size == 0:
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # ---------- SAVE FULL VEHICLE (DEBUG) ----------
    veh_dir = os.path.join(VEHICLE_DIR, f"vehicle_{v_id}")
    os.makedirs(veh_dir, exist_ok=True)
    cv2.imwrite(os.path.join(veh_dir, f"{ts}_vehicle.jpg"), vehicle_crop)

    # ---------- PLATE DETECTION ----------
    plate_boxes = plate_detector.detect(vehicle_crop, conf=0.2)

    if not plate_boxes:
        return  

    # ---------- PROCESS EACH PLATE ----------
    for px1, py1, px2, py2, det_conf in plate_boxes:
        plate_crop = vehicle_crop[py1:py2, px1:px2]
        if plate_crop.size == 0:
            continue

        h, w = plate_crop.shape[:2]
        if w < MIN_PLATE_WIDTH:
            continue

        sharpness = get_blur_score(plate_crop)
        if sharpness < MIN_SHARPNESS:
            continue

        # Composite score: higher = clearer plate and higher detection certainty
        score = sharpness * det_conf

        # ---------- UPDATE BUFFER ----------
        car_buffer[v_id].append((score, plate_crop))
        
        # Sort buffer by score descending and keep only the top N images
        car_buffer[v_id] = sorted(
            car_buffer[v_id],
            key=lambda x: x[0],
            reverse=True
        )[:MAX_PLATES_PER_VEHICLE]

        # ---------- EARLY STOP (THE WINNER) ----------
        if score >= BEST_SCORE_THRESHOLD:
            print(f"🏁 LOCKED: High quality plate for vehicle {v_id} (Score: {score:.1f})")

            locked_ids.add(v_id)

            if not task_queue.full():
                # Save the images being sent to OCR
                save_ocr_batch(v_id, car_buffer[v_id])
                
                # Send the whole list of best images to the worker
                task_queue.put((v_id, car_buffer[v_id]))
                processed_ids.add(v_id)

            # Cleanup memory
            car_buffer.pop(v_id, None)
            first_seen_time.pop(v_id, None)
            return
