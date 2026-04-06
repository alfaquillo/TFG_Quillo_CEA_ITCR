import os
import numpy as np
import math

MODEL_PATH = "lunar_rpi5_float16.tflite"
IMAGE_DIR = "dataset_test"
SAVE_DIR = "results"

DEBUG = True
SAVE_IMAGES = True

IMG_DATASET_H = 240
IMG_DATASET_W = 320

MODEL_H = 240
MODEL_W = 320

NAV_CLASSES = [0]
FRAMES_PER_DECISION = 3
USE_TRAPEZOID = True

# SLAM
CELL_M = 0.5
MAP_W_M, MAP_H_M = 40, 40

MAP_W = int(MAP_W_M / CELL_M)
MAP_H = int(MAP_H_M / CELL_M)

UNKNOWN = 255
TRACE = 254
ROVER = 253

TURN_ANGLE_DEG = 2
STEP_METERS = 0.5

os.makedirs(SAVE_DIR, exist_ok=True)