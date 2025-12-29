from ultralytics import YOLO

class PlateDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, img, conf=0.3):
        """
        Returns: list of (x1, y1, x2, y2, conf)
        """
        results = self.model(img, conf=conf, verbose=False)[0]
        boxes = []

        if results.boxes is not None:
            xyxy = results.boxes.xyxy.cpu().numpy()
            confs = results.boxes.conf.cpu().numpy()

            for box, c in zip(xyxy, confs):
                x1, y1, x2, y2 = map(int, box)
                boxes.append((x1, y1, x2, y2, float(c)))

        return boxes
