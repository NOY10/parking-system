from ultralytics import YOLO

class VehicleDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        try:
            self.model.to("cuda")
            print("✅ YOLO using GPU")
        except:
            print("⚠ YOLO using CPU")

    def detect(self, frame):
        return self.model(frame, imgsz=640, conf=0.4, verbose=False)[0]
