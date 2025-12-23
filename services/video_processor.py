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
    mask = None

    try:
        while True:
            if capture.latest_frame is None:
                time.sleep(0.01)
                continue

            # 1. ORIGINAL FRAME for visual display (No black mask)
            display_frame = capture.latest_frame.copy()
            frame_count += 1

            # 2. Setup ROI mask once
            if mask is None:
                mask = np.zeros(display_frame.shape[:2], dtype=np.uint8)
                roi_corners = np.array([SRC_POINTS], dtype=np.int32)
                cv2.fillPoly(mask, roi_corners, 255)

            # 3. Create HIDDEN MASKED FRAME for YOLO only
            # This is never shown to the user, so no flickering occurs
            detection_input = cv2.bitwise_and(display_frame, display_frame, mask=mask)

            # 4. FRAME SKIP Logic
            if frame_count % FRAME_SKIP != 0:
                with lock:
                    shared_state["latest_frame"] = display_frame
                continue

            # 5. YOLO detection on the MASKED frame
            results = detector.detect(detection_input)
            occupied, bev_points = compute_occupied(results, BEV_SLOTS, transformer)
            stable = debouncer.update(occupied)

            # 6. Logic & Timers
            timers.update(stable, previous)
            previous = stable.copy()
            slots_detail = timers.build_slot_details(stable)

            # 7. DRAWING - We draw everything on the CLEAN display_frame
            draw_slots(display_frame, SLOTS, stable)
            draw_ground_points(display_frame, results, VEHICLE_CLASSES)
            draw_homography_roi(display_frame, SRC_POINTS) # Draw ROI border for reference
            
            # 8. BEV View remains in its own window
            bev_view = draw_bev_view(stable, bev_points, BEV_SLOTS)
            cv2.imshow("BEV - Parking Map", bev_view)
            cv2.waitKey(1)

            # 9. Update Shared State with the CLEAN frame
            with lock:
                shared_state["latest_frame"] = display_frame
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
