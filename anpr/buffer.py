import cv2
import os
from anpr.worker import task_queue
from config.settings import BUFFER_SIZE

car_buffer = {}
processed = set()
processed_ids = set()
final_results = {}

# def update_anpr(v_id, frame, box):
#     x1, y1, x2, y2 = map(int, box)
    
#     if v_id not in final_results and v_id not in processed_ids:
#         if v_id not in car_buffer: car_buffer[v_id] = []
#         if len(car_buffer[v_id]) < BUFFER_SIZE:
#             car_buffer[v_id].append(frame[y1:y2, x1:x2].copy())
#         elif len(car_buffer[v_id]) == BUFFER_SIZE:
#             if not task_queue.full():
#                 task_queue.put((v_id, car_buffer[v_id]))
#                 processed_ids.add(v_id)
#             car_buffer.pop(v_id, None)


import os
import cv2
from datetime import datetime

# Ensure a debug folder exists
DEBUG_DIR = "Debug_img"
os.makedirs(DEBUG_DIR, exist_ok=True)

def update_anpr(v_id, frame, box):
    x1, y1, x2, y2 = map(int, box)
    
    if v_id not in final_results and v_id not in processed_ids:
        if v_id not in car_buffer: car_buffer[v_id] = []
        
        if len(car_buffer[v_id]) < BUFFER_SIZE:
            # Create the crop
            crop = frame[y1:y2, x1:x2].copy()
            car_buffer[v_id].append(crop)

            # ---------- SAVE FOR DEBUG ----------
            # Format: debug_crops/ID_1_20251226_111530_123456_crop_0.jpg
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            crop_index = len(car_buffer[v_id]) - 1
            filename = f"ID_{v_id}_{timestamp}_crop_{crop_index}.jpg"
            save_path = os.path.join(DEBUG_DIR, filename)
            
            cv2.imwrite(save_path, crop)
            # ------------------------------------

        elif len(car_buffer[v_id]) == BUFFER_SIZE:
            if not task_queue.full():
                task_queue.put((v_id, car_buffer[v_id]))
                processed_ids.add(v_id)
            car_buffer.pop(v_id, None)