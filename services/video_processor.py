# import time
# import threading
# import cv2

# from camera.rtsp_capture import RTSPCapture
# from detection.yolo_detector import VehicleDetector
# from bev.homography import BEVTransformer
# from parking.slots import load_slots, transform_slots
# from parking.occupancy import compute_occupied
# from parking.debounce import Debouncer
# from parking.timers import SlotTimers
# from config.settings import *
# from state.shared_state import shared_state, lock

# #debug
# from parking.renderer import (
#     draw_slots,
#     draw_ground_points,
#     draw_homography_roi,
#     draw_bev_view,
#     draw_vehicle_analytics
# )
# from config.settings import VEHICLE_CLASSES,SRC_POINTS

# capture = RTSPCapture(VIDEO_SOURCE)
# detector = VehicleDetector(MODEL_PATH)
# transformer = BEVTransformer(H_MATRIX)

# SLOTS = load_slots()
# BEV_SLOTS = transform_slots(SLOTS)

# debouncer = Debouncer(SLOTS.keys(), MIN_FRAMES_FOR_CHANGE)
# timers = SlotTimers(SLOTS.keys())

# previous = set()
# frame_count = 0

# def process_loop():
#     global previous, frame_count
#     mask = None

#     try:
#         while True:
#             if capture.latest_frame is None:
#                 time.sleep(0.01)
#                 continue

#             # 1. ORIGINAL FRAME for visual display (No black mask)
#             display_frame = capture.latest_frame.copy()
#             frame_count += 1

#             # 2. Setup ROI mask once
#             if mask is None:
#                 mask = np.zeros(display_frame.shape[:2], dtype=np.uint8)
#                 roi_corners = np.array([SRC_POINTS], dtype=np.int32)
#                 cv2.fillPoly(mask, roi_corners, 255)

#             # 3. Create HIDDEN MASKED FRAME for YOLO only
#             # This is never shown to the user, so no flickering occurs
#             detection_input = cv2.bitwise_and(display_frame, display_frame, mask=mask)

#             # 4. FRAME SKIP Logic
#             if frame_count % FRAME_SKIP != 0:
#                 with lock:
#                     shared_state["latest_frame"] = display_frame
#                 continue

#             # 5. YOLO detection on the MASKED frame
#             # results = detector.detect(detection_input)
#             results = detector.model.track(detection_input, persist=True, classes=[2,3,5,7], verbose=False)[0]

#             # # --- DATA LOGIC (ANPR Buffering) ---
#             # if results.boxes.id is not None:
#             #     handle_anpr_buffering(results, display_frame) # Call your buffer logic here


#             #6. --- PARKING LOGIC ---
#             occupied, bev_points = compute_occupied(results, BEV_SLOTS, transformer)
#             stable = debouncer.update(occupied)
#             timers.update(stable, previous)
#             previous = stable.copy()
#             slots_detail = timers.build_slot_details(stable)

#             # 7. DRAWING 
#             draw_slots(display_frame, SLOTS, stable)
#             draw_ground_points(display_frame, results, VEHICLE_CLASSES)
#             draw_homography_roi(display_frame, SRC_POINTS) # Draw ROI border for reference
#             draw_vehicle_analytics(display_frame, results, {})
            
#             # 8. BEV View remains in its own window
#             bev_view = draw_bev_view(stable, bev_points, BEV_SLOTS)
#             cv2.imshow("BEV - Parking Map", bev_view)
#             cv2.waitKey(1)

#             # 9. Update Shared State with the CLEAN frame
#             with lock:
#                 shared_state["latest_frame"] = display_frame
#                 shared_state["current_status"].update({
#                     "total": len(SLOTS),
#                     "occupied": len(stable),
#                     "free": len(SLOTS) - len(stable),
#                     "occupied_slots": list(stable),
#                     "slots": slots_detail
#                 })

#             time.sleep(0.05)

#     except Exception as e:
#         print("❌ process_loop crashed:", e)


# def start_video_thread():
#     print("🚀 start_video_thread called")
#     threading.Thread(target=capture.run, daemon=True).start()
#     threading.Thread(target=process_loop, daemon=True).start()



import time
import threading
import cv2

from camera.rtsp_capture import RTSPCapture
from camera.VideoFileCapture import VideoFileCapture
from detection.yolo_detector import VehicleDetector
from bev.homography import BEVTransformer
from parking.slots import load_slots, transform_slots
from parking.occupancy import compute_occupied
from parking.debounce import Debouncer
from parking.timers import SlotTimers
from config.settings import *
from state.shared_state import shared_state, lock

#db_manager
from database.manager import db_manager

from anpr.buffer import update_anpr

from anpr.worker import anpr_worker_thread
from anpr.buffer import task_queue

#debug
from parking.renderer import (
    draw_slots,
    draw_ground_points,
    draw_homography_roi,
    draw_bev_view,
    draw_vehicle_analytics
)
from config.settings import VEHICLE_CLASSES,SRC_POINTS

# capture = VideoFileCapture(VIDEO_SOURCE)
capture = RTSPCapture(VIDEO_SOURCE)
detector = VehicleDetector(MODEL_PATH)
transformer = BEVTransformer(H_MATRIX)

SLOTS = load_slots()
BEV_SLOTS = transform_slots(SLOTS)

debouncer = Debouncer(SLOTS.keys(), MIN_FRAMES_FOR_CHANGE)
timers = SlotTimers(SLOTS.keys(), db_manager=db_manager)

previous = set()
frame_count = 0

#Persistent State
last_yolo_results = None

def process_loop():
    global previous, frame_count, last_yolo_results
    
    mask = None
    stable = set()
    bev_points = []

    try:
        while True:
            if capture.latest_frame is None:
                time.sleep(0.01)
                continue

            display_frame = capture.latest_frame.copy()
            frame_count += 1

            # --- UPDATED ROI MASK LOGIC ---
            if mask is None:
                mask = np.zeros(display_frame.shape[:2], dtype=np.uint8)
                # Use ROI_POINTS (5 points) for the polygon mask
                roi_corners = np.array([ROI_POINTS], dtype=np.int32)
                cv2.fillPoly(mask, roi_corners, 255)

            # 4. HEAVY LOGIC
            if frame_count % FRAME_SKIP == 0:
                # Mask the input so YOLO only sees inside your 5-point pentagon
                detection_input = cv2.bitwise_and(display_frame, display_frame, mask=mask)
                
                results = detector.model.track(detection_input, persist=True, classes=[2], verbose=False)
                
                if results and len(results) > 0:
                    last_yolo_results = results[0]

                    try:
                        # Homography still works using the 4-point H_MATRIX
                        occupied, bev_points, slot_vehicle_map = compute_occupied(last_yolo_results, BEV_SLOTS, transformer)
                        stable = debouncer.update(occupied)
                        timers.update(stable, previous, slot_vehicle_map)
                        previous = stable.copy()
                    except ValueError as e:
                        print(f"⚠️ Skipping occupancy: {e}")
                        occupied, bev_points = set(), []
                    
                    slots_detail = timers.build_slot_details(stable)

                    # --- ANPR ---
                    if last_yolo_results.boxes.id is not None:
                        boxes = last_yolo_results.boxes.xyxy.cpu().numpy()
                        ids = last_yolo_results.boxes.id.int().cpu().numpy()                                    
                        for box, v_id in zip(boxes, ids):
                            update_anpr(v_id, display_frame, box)

                    with lock:
                        shared_state["current_status"].update({
                            "total": len(SLOTS),
                            "occupied": len(stable),
                            "free": len(SLOTS) - len(stable),
                            "occupied_slots": list(stable),
                            "slots": slots_detail
                        })
                        current_plates = shared_state.get("anpr_results", {}).copy()

            # 5. DRAWING
            if last_yolo_results is not None:
                draw_slots(display_frame, SLOTS, stable)
                draw_ground_points(display_frame, last_yolo_results, VEHICLE_CLASSES)
                # Draw the ROI boundary (5 points)
                draw_homography_roi(display_frame, ROI_POINTS) 
                draw_vehicle_analytics(display_frame, last_yolo_results, current_plates)

                bev_view = draw_bev_view(stable, bev_points, BEV_SLOTS)
                cv2.imshow("BEV - Parking Map", bev_view)
                cv2.waitKey(1)

            with lock:
                shared_state["latest_frame"] = display_frame

            time.sleep(0.01)

    except Exception as e:
        print("❌ process_loop crashed:", e)

# start_anpr_worker()

# def process_loop():
#     global previous, frame_count, last_yolo_results
    
#     # --- 1. INITIALIZE VARIABLES BEFORE THE LOOP ---
#     mask = None
#     stable = set()
#     bev_points = []
#     # -----------------------------------------------

#     try:
#         while True:
#             if capture.latest_frame is None:
#                 time.sleep(0.01)
#                 continue

#             # 2. Always get a fresh frame for the display
#             display_frame = capture.latest_frame.copy()
#             frame_count += 1

#             # 3. Setup ROI mask once (Local scope initialization)
#             if mask is None:
#                 mask = np.zeros(display_frame.shape[:2], dtype=np.uint8)
#                 roi_corners = np.array([SRC_POINTS], dtype=np.int32)
#                 cv2.fillPoly(mask, roi_corners, 255)

#             # 4. HEAVY LOGIC (Only run every FRAME_SKIP frames)
#             if frame_count % FRAME_SKIP == 0:
#                 detection_input = cv2.bitwise_and(display_frame, display_frame, mask=mask)
                
#                 # YOLO tracking
#                 results = detector.model.track(detection_input, persist=True, classes=[2], verbose=False)
                
#                 if results and len(results) > 0:
#                     last_yolo_results = results[0]

#                     # --- PARKING LOGIC ---
#                     # Update 'stable' and 'bev_points' here
#                     try:
#                         occupied, bev_points, slot_vehicle_map  = compute_occupied(last_yolo_results, BEV_SLOTS, transformer)
#                         stable = debouncer.update(occupied)
#                         timers.update(stable, previous,slot_vehicle_map)
#                         previous = stable.copy()
#                     except ValueError as e:
#                         print(f"⚠️ Skipping occupancy calculation: {e}")
#                         occupied, bev_points = set(), []
#                     slots_detail = timers.build_slot_details(stable)

#                     # --- ANPR INTEGRATION ---
#                     if last_yolo_results.boxes.id is not None:
#                         boxes = last_yolo_results.boxes.xyxy.cpu().numpy()
#                         ids = last_yolo_results.boxes.id.int().cpu().numpy()                                    
#                          # Use your new buffer utility
#                         for box, v_id in zip(boxes, ids):
#                             update_anpr(v_id, display_frame, box)

#                     # Update shared status
#                     with lock:
#                         shared_state["current_status"].update({
#                             "total": len(SLOTS),
#                             "occupied": len(stable),
#                             "free": len(SLOTS) - len(stable),
#                             "occupied_slots": list(stable),
#                             "slots": slots_detail
#                         })
#                         current_plates = shared_state.get("anpr_results", {}).copy()

#             # 5. DRAWING (Runs EVERY frame - using latest known data)
#             # This prevents flickering because we draw even on skipped frames
#             if last_yolo_results is not None:
#                 draw_slots(display_frame, SLOTS, stable)
#                 draw_ground_points(display_frame, last_yolo_results, VEHICLE_CLASSES)
#                 draw_homography_roi(display_frame, SRC_POINTS)
#                 draw_vehicle_analytics(display_frame, last_yolo_results, current_plates)

#                 # print("current_plates",current_plates)
                
#                 # 6. BEV View update
#                 bev_view = draw_bev_view(stable, bev_points, BEV_SLOTS)
#                 cv2.imshow("BEV - Parking Map", bev_view)
#                 cv2.waitKey(1)

#             # 7. Update Shared State with the DRAWN frame
#             with lock:
#                 shared_state["latest_frame"] = display_frame

#             # Minimal sleep to keep CPU usage sane
#             time.sleep(0.01)

#     except Exception as e:
#         print("❌ process_loop crashed:", e)


def start_video_thread():
    print("🚀 start_video_thread called")
    threading.Thread(target=capture.run, daemon=True).start()
    threading.Thread(target=process_loop, daemon=True).start()
    ocr_thread = threading.Thread(target=anpr_worker_thread, args=(task_queue,), daemon=True)
    ocr_thread.start()