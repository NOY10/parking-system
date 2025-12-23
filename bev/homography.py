import cv2
import numpy as np

class BEVTransformer:
    def __init__(self, H):
        self.H = H

    def transform_point(self, x, y):
        pt = np.array([[[x, y]]], dtype=np.float32)
        return cv2.perspectiveTransform(pt, self.H)[0][0]
