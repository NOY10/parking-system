import cv2
import numpy as np
from config.settings import VEHICLE_CLASSES

def compute_occupied(results, bev_slots, transformer):
    occupied = set()

    bev_points = [] # To store points for the debug window

    if not results.boxes:
        return occupied

    for box, cls in zip(results.boxes.xyxy.cpu().numpy(),
                        results.boxes.cls.cpu().numpy()):
        if int(cls) not in VEHICLE_CLASSES:
            continue

        x1, y1, x2, y2 = box.astype(int)
        bx, by = transformer.transform_point((x1+x2)//2, y2)

        bev_points.append((int(bx), int(by)))

        for sid, poly in bev_slots.items():
            if cv2.pointPolygonTest(poly, (int(bx), int(by)), False) >= 0:
                occupied.add(sid)
                break

    return occupied,bev_points
