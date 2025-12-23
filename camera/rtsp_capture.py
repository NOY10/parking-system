import cv2
import time

class RTSPCapture:
    def __init__(self, source):
        self.source = source
        self.latest_frame = None

    def run(self):
        cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        print("🟢 RTSP capture started")
        while True:
            ret, frame = cap.read()
            if ret:
                self.latest_frame = frame
            else:
                cap.release()
                time.sleep(1)
                cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
