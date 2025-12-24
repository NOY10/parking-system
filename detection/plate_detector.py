from ultralytics import YOLO

class PlateDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, img):
        results = self.model(img, conf=0.15, verbose=False)[0]
        boxes = []

        if results.boxes is not None:
            for box in results.boxes.xyxy.cpu().numpy():
                boxes.append(list(map(int, box)))

        return boxes
