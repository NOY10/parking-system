# import cv2
# import numpy as np
# from config.settings import VEHICLE_CLASSES

# def compute_occupied(results, bev_slots, transformer):
#     occupied = set()

#     bev_points = [] # To store points for the debug window

#     if not results.boxes:
#         return occupied

#     for box, cls in zip(results.boxes.xyxy.cpu().numpy(),
#                         results.boxes.cls.cpu().numpy()):
#         if int(cls) not in VEHICLE_CLASSES:
#             continue

#         x1, y1, x2, y2 = box.astype(int)
#         bx, by = transformer.transform_point((x1+x2)//2, y2)

#         bev_points.append((int(bx), int(by)))

#         for sid, poly in bev_slots.items():
#             if cv2.pointPolygonTest(poly, (int(bx), int(by)), False) >= 0:
#                 occupied.add(sid)
#                 break

#     return occupied,bev_points


import cv2
import numpy as np
from config.settings import VEHICLE_CLASSES


def compute_occupied(results, bev_slots, transformer):
    occupied = set()
    bev_points = []
    slot_vehicle_map = {}

    if results is None or results.boxes is None:
        return occupied, bev_points, slot_vehicle_map

    # Track IDs may be None in first frames
    if results.boxes.id is None:
        return occupied, bev_points, slot_vehicle_map

    boxes = results.boxes.xyxy.cpu().numpy()
    classes = results.boxes.cls.cpu().numpy()
    track_ids = results.boxes.id.int().cpu().numpy()

    for box, cls, track_id in zip(boxes, classes, track_ids):
        if int(cls) not in VEHICLE_CLASSES:
            continue

        x1, y1, x2, y2 = box.astype(int)

        # Use bottom-center of bbox (best for parking)
        cx = (x1 + x2) // 2
        cy = y2

        # Transform to BEV space
        bx, by = transformer.transform_point(cx, cy)
        bx, by = int(bx), int(by)

        bev_points.append((bx, by))

        # Check which slot this vehicle occupies
        for sid, poly in bev_slots.items():
            if cv2.pointPolygonTest(poly, (bx, by), False) >= 0:
                occupied.add(sid)

                # 🔑 KEY LINE: slot → vehicle mapping
                slot_vehicle_map[sid] = int(track_id)
                break

    return occupied, bev_points, slot_vehicle_map
