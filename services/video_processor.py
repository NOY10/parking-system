import time
import threading
import cv2

from camera.rtsp_capture import RTSPCapture
from detection.yolo_detector import VehicleDetector
from bev.homography import BEVTransformer
from parking.slots import load_slots, transform_slots
from parking.occupancy import compute_occupied
from parking.debounce import Debouncer
from parking.timers import SlotTimers
from config.settings import *
from state.shared_state import shared_state, lock

#debug
from parking.renderer import (
    draw_slots,
    draw_ground_points,
    draw_homography_roi,
    draw_bev_view
)
from config.settings import VEHICLE_CLASSES,SRC_POINTS

capture = RTSPCapture(VIDEO_SOURCE)
detector = VehicleDetector(MODEL_PATH)
transformer = BEVTransformer(H_MATRIX)

SLOTS = load_slots()
BEV_SLOTS = transform_slots(SLOTS)

debouncer = Debouncer(SLOTS.keys(), MIN_FRAMES_FOR_CHANGE)
timers = SlotTimers(SLOTS.keys())

previous = set()
frame_count = 0


def process_loop():
    global previous, frame_count

    try:
        while True:
            if capture.latest_frame is None:
                time.sleep(0.01)
                continue

            frame = capture.latest_frame.copy()
            frame_count += 1

            # FRAME SKIP
            if frame_count % FRAME_SKIP != 0:
                with lock:
                    shared_state["latest_frame"] = frame
                continue

            # YOLO detection
            results = detector.detect(frame)
            occupied, bev_points = compute_occupied(results, BEV_SLOTS, transformer)
            stable = debouncer.update(occupied)

            # Timers
            timers.update(stable, previous)
            previous = stable.copy()

            # ✅ build slots_detail AFTER stable exists
            slots_detail = timers.build_slot_details(stable)

            draw_slots(frame, SLOTS, stable)
            draw_ground_points(frame, results, VEHICLE_CLASSES)
            draw_homography_roi(frame, SRC_POINTS)
            
            bev_view = draw_bev_view(stable, bev_points, BEV_SLOTS)
            cv2.imshow("BEV - Parking Map", bev_view)
            cv2.waitKey(1)

            with lock:
                shared_state["latest_frame"] = frame
                shared_state["current_status"].update({
                    "total": len(SLOTS),
                    "occupied": len(stable),
                    "free": len(SLOTS) - len(stable),
                    "occupied_slots": list(stable),
                    "slots": slots_detail
                })

            time.sleep(0.05)

    except Exception as e:
        print("❌ process_loop crashed:", e)

def start_video_thread():
    print("🚀 start_video_thread called")
    threading.Thread(target=capture.run, daemon=True).start()
    threading.Thread(target=process_loop, daemon=True).start()
