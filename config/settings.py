import os
import numpy as np
import cv2

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay|stimeout;5000000"
)

VIDEO_SOURCE = "rtsp://onvifuser:bht%402025@192.168.1.6:554/Streaming/Channels/101?transportmode=unicast&profile=Profile_1"
MODEL_PATH = "yolo11n.pt"
SLOTS_JSON_FILE = "detection/parking_slots.json"

VEHICLE_CLASSES = {2, 3, 5, 7}

FRAME_SKIP = 4
MIN_FRAMES_FOR_CHANGE = 3

# BEV
SRC_POINTS = np.float32([
    [646, 419],
    [496, 1438],
    [2558, 1438],
    [2558, 169]
])

BEV_WIDTH, BEV_HEIGHT = 800, 600

DST_POINTS = np.float32([
    [0, 0],
    [BEV_WIDTH, 0],
    [BEV_WIDTH, BEV_HEIGHT],
    [0, BEV_HEIGHT]
])

H_MATRIX = cv2.getPerspectiveTransform(SRC_POINTS, DST_POINTS)
