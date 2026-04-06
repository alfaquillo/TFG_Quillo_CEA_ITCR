import cv2
import numpy as np
import math
from config import *
import slam 


# ==============================
# SEGMENTACIÓN 
# ==============================
def colorize_mask(mask):
    colors = np.array([
        [60, 60, 60],
        [0, 255, 255],
        [0, 0, 255],
        [255, 200, 0],
        [0, 255, 0]
    ], dtype=np.uint8)

    return colors[mask]


# ==============================
# SLAM VIEW
# ==============================
def draw_slam():

    grid = slam.grid
    rx, ry = slam.meters_to_cell()
    theta = slam.theta

    colors = np.array([
        [60, 60, 60],
        [0, 255, 255],
        [0, 0, 255],
        [255, 200, 0],
        [255,255,0]
    ], dtype=np.uint8)

    vis = np.zeros((slam.MAP_H, slam.MAP_W, 3), dtype=np.uint8)

    known = (grid != UNKNOWN) & (grid != TRACE)
    vis[known] = colors[grid[known]]

    vis[grid == UNKNOWN] = (40,40,40)
    vis[grid == TRACE]   = (255,0,255)

    # ===============================
    # VENTANA CENTRADA ROBUSTA
    # ===============================
    VIEW = 120
    half = VIEW // 2

    canvas = np.zeros((VIEW, VIEW, 3), dtype=np.uint8)

    for dy in range(-half, half):
        for dx in range(-half, half):

            gx = rx + dx
            gy = ry + dy

            cx = dx + half
            cy = dy + half

            if 0 <= gx < slam.MAP_W and 0 <= gy < slam.MAP_H:
                canvas[cy, cx] = vis[gy, gx]
            else:
                canvas[cy, cx] = (0, 0, 0)

    # rover
    canvas[half, half] = (0,255,0)


    return cv2.resize(canvas, None, fx=6, fy=6, interpolation=cv2.INTER_NEAREST)