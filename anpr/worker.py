import threading
from queue import Queue
from detection.plate_detector import PlateDetector
from anpr.ocr import extract_plate
from config.settings import *
# from database.plate_db import PlateDatabase
from state.shared_state import shared_state, lock

task_queue = Queue(maxsize=15)

def start_anpr_worker():
    threading.Thread(target=_worker, daemon=True).start()

def _worker():
    plate_detector = PlateDetector(LPD_PATH)

    while True:
        task = task_queue.get()
        if task is None:
            break

        v_id, vehicle_crops = task
        ocr_inputs = []

        # =============================
        # 1️⃣ Plate detection
        # =============================
        for vehicle_img in vehicle_crops:
            detections = plate_detector.detect(vehicle_img)

            for box in detections:
                x1, y1, x2, y2 = box
                plate_crop = vehicle_img[y1:y2, x1:x2]

                ocr_inputs.append({
                    "img": vehicle_img,
                    "plate": plate_crop,
                    "box": box
                })

        # =============================
        # 2️⃣ OCR + regex voting
        # =============================
        plate, bbox = extract_plate(ocr_inputs)

        if plate:
            with lock:
                shared_state["anpr_results"][v_id] = {
                    "plate": plate,
                    "bbox": bbox
                }

        task_queue.task_done()
