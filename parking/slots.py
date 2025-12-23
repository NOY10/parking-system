import json
import numpy as np
import cv2
from config.settings import SLOTS_JSON_FILE, H_MATRIX

def load_slots():
    with open(SLOTS_JSON_FILE, "r") as f:
        data = json.load(f)

    return {
        int(slot["id"]): np.array(slot["points"], dtype=np.int32)
        for slot in data
    }

def transform_slots(slots):
    bev_slots = {}
    for sid, poly in slots.items():
        pts = poly.astype("float32").reshape(-1, 1, 2)
        bev_slots[sid] = cv2.perspectiveTransform(pts, H_MATRIX).reshape(-1, 2).astype("int32")
    return bev_slots
