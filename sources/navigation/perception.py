import cv2
import numpy as np
from config import *

def preprocess(img, input_details):
    img = cv2.resize(img, (MODEL_W, MODEL_H))

    dtype = input_details[0]["dtype"]

    if dtype == np.uint8:
        img = img.astype(np.uint8)
    else:
        img = img.astype(np.float32) / 255.0

    return np.expand_dims(img, 0)


def create_navigation_mask(mask):
    return np.isin(mask, NAV_CLASSES).astype(np.uint8)


def trapezoid_roi(shape):
    h, w = shape

    if not USE_TRAPEZOID:
        return np.ones((h, w), dtype=np.uint8), None

    mask = np.zeros((h, w), dtype=np.uint8)

    pts = np.array([
        (int(w*0.15), int(h*0.10)),
        (int(w*0.85), int(h*0.10)),
        (int(w*0.98), int(h*0.50)),
        (int(w*0.02), int(h*0.50))
    ], dtype=np.int32)

    cv2.fillPoly(
        img=mask,
        pts=[pts.astype(np.int32)],
        color=(1,)
    )
    return mask, pts