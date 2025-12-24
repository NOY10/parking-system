import cv2
import numpy as np
from config.settings import BEV_HEIGHT, BEV_WIDTH

# ===============================
# CAMERA VIEW
# ===============================

def draw_slots(frame, slots, occupied):
    for sid, poly in slots.items():
        color = (0, 0, 255) if sid in occupied else (0, 255, 0)
        cv2.polylines(frame, [poly], True, color, 2)

def draw_ground_points(frame, results, vehicle_classes):
    if not results.boxes:
        return

    for box, cls in zip(results.boxes.xyxy.cpu().numpy(),
                        results.boxes.cls.cpu().numpy()):
        if int(cls) in vehicle_classes:
            x1, y1, x2, y2 = box.astype(int)
            cv2.circle(frame, ((x1+x2)//2, y2), 4, (255, 0, 255), -1)

def draw_homography_roi(frame, src_points):
    # 1. Convert points to integer for OpenCV
    pts_int = src_points.astype(np.int32)
    
    # 2. Draw the Polygon (OUTSIDE the for loop)
    cv2.polylines(frame, [pts_int], isClosed=True, color=(255, 0, 0), thickness=2)
    
    # 3. Draw individual points and labels
    for i, (x, y) in enumerate(pts_int):
        cv2.circle(frame, (x, y), 8, (255, 0, 0), -1)
        cv2.putText(
            frame, 
            f"P{i+1}", 
            (x + 5, y - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.8, 
            (255, 0, 0), 
            2
        )

# # ===============================
# # BEV VIEW
# # ===============================
def draw_bev_view(occupied_slots, bev_points,bev_slots):
    """
    occupied_slots: set of occupied slot IDs
    bev_points: list of (x, y) vehicle ground points in BEV space
    """
    bev = np.zeros((BEV_HEIGHT, BEV_WIDTH, 3), dtype=np.uint8)

    # Draw parking slots
    for slot_id, poly in bev_slots.items():
        color = (0, 0, 255) if slot_id in occupied_slots else (0, 255, 0)
        cv2.polylines(bev, [poly], True, color, 2)

        # Slot ID label
        cx, cy = poly.mean(axis=0).astype(int)
        cv2.putText(
            bev, f"S{slot_id}",
            (cx - 10, cy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5, color, 1
        )

    # Draw vehicle points
    for x, y in bev_points:
        cv2.circle(bev, (x, y), 5, (255, 0, 255), -1)

    return bev

def draw_vehicle_analytics(frame, results, final_results):
    """
    Draws tracking IDs, Bounding Boxes, and detected Plates.
    If plate is not in final_results, shows 'Scanning...'
    """
    # 1. Check if we actually have tracking results
    if results.boxes is None or results.boxes.id is None:
        return frame

    # 2. Extract tracking data
    ids = results.boxes.id.int().cpu().numpy()
    boxes = results.boxes.xyxy.cpu().numpy()
    clss = results.boxes.cls.int().cpu().numpy()

    for v_id, box, cls_idx in zip(ids, boxes, clss):
        x1, y1, x2, y2 = map(int, box)
        
        # 3. Logic: Check if we have a plate for this specific ID
        # If final_results is not a dict or ID not in it, show "Scanning..."
        if isinstance(final_results, dict) and v_id in final_results:
            plate_text = final_results[v_id]
            color = (0, 255, 0)  # Green for found
        else:
            plate_text = "Scanning..."
            color = (0, 165, 255) # Orange for searching

        # 4. Draw Bounding Box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # 5. Draw Label (ID + Plate)
        label = f"ID:{v_id} | {plate_text}"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        
        # Label background
        cv2.rectangle(frame, (x1, y1 - h - 15), (x1 + w, y1), color, -1)
        # White text on the color background
        cv2.putText(frame, label, (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
    return frame