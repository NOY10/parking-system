import threading
from queue import Queue
from detection.plate_detector import PlateDetector
from anpr.ocr import extract_plate
from database.plate_db import PlateDatabase
from state.shared_state import shared_state, lock

task_queue = Queue(maxsize=15)

def start_anpr_worker():
    threading.Thread(target=_worker, daemon=True).start()

def _worker():
    detector = PlateDetector()
    db = PlateDatabase()

    while True:
        task = task_queue.get()
        if task is None:
            break

        v_id, crops = task
        plate, bbox = extract_plate(crops)

        if plate:
            with lock:
                shared_state["anpr_results"][v_id] = {
                    "plate": plate,
                    "bbox": bbox
                }
            db.save_to_db(v_id, plate, f"detections/ID_{v_id}.jpg")

        task_queue.task_done()
