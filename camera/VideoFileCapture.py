import cv2
import time

class VideoFileCapture:
    def __init__(self, source):
        # source will now be a file path like "data/test_video.mp4"
        self.source = source
        self.latest_frame = None

    def run(self):
        # For local files, we usually don't need CAP_FFMPEG explicitly, 
        # and BUFFERSIZE is ignored for static files.
        cap = cv2.VideoCapture(self.source)
        
        if not cap.isOpened():
            print(f"🔴 Error: Could not open video file {self.source}")
            return

        print(f"🔵 Local video testing started: {self.source}")
        
        while True:
            ret, frame = cap.read()
            
            if ret:
                self.latest_frame = frame
                # IMPORTANT: Local files read faster than real-time.
                # Adding a small sleep prevents the CPU from hitting 100% 
                # and keeps the playback speed somewhat realistic.
                time.sleep(0.01) 
            else:
                # Video reached the end: Seek back to the first frame to loop
                print("🔄 Video ended, restarting loop...")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                
                # Small pause before restarting to avoid a crash if the file is locked
                time.sleep(1)

        cap.release()