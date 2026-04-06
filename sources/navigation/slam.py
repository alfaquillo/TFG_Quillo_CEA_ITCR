import numpy as np
import math
from config import *

# ==============================
# ESTADO
# ==============================
grid = np.full((MAP_H, MAP_W), UNKNOWN, dtype=np.uint8)

x_m, y_m = 0.0, 0.0
theta = math.pi / 2

origin_x = MAP_W // 2
origin_y = MAP_H // 2

trajectory = [(x_m, y_m, theta)]


# ==============================
# COORDENADAS
# ==============================
def meters_to_cell():
    rx = int(origin_x + x_m / CELL_M)
    ry = int(origin_y - y_m / CELL_M)
    return rx, ry


# ==============================
# EXPANSIÓN
# ==============================
def expand_map_if_needed(rx, ry):
    global grid, origin_x, origin_y, MAP_W, MAP_H

    pad = 40

    expand_left   = rx < 5
    expand_right  = rx > MAP_W - 6
    expand_top    = ry < 5
    expand_bottom = ry > MAP_H - 6

    if not (expand_left or expand_right or expand_top or expand_bottom):
        return

    new_h = MAP_H + pad*(expand_top + expand_bottom)
    new_w = MAP_W + pad*(expand_left + expand_right)

    new_grid = np.full((new_h, new_w), UNKNOWN, dtype=np.uint8)

    off_y = pad if expand_top else 0
    off_x = pad if expand_left else 0

    new_grid[off_y:off_y+MAP_H, off_x:off_x+MAP_W] = grid

    grid = new_grid
    MAP_H, MAP_W = new_grid.shape

    origin_x += off_x
    origin_y += off_y


# ==============================
# MOVIMIENTO
# ==============================
def move_rover(decision):
    global x_m, y_m, theta

    if decision == "IZQUIERDA":
        theta += math.radians(TURN_ANGLE_DEG)
    elif decision == "DERECHA":
        theta -= math.radians(TURN_ANGLE_DEG)

    x_m += STEP_METERS * math.cos(theta)
    y_m += STEP_METERS * math.sin(theta)

    trajectory.append((x_m, y_m, theta))


# ==============================
# INTEGRACIÓN OBSERVACIÓN 
# ==============================
def integrate_observation(mask):

    rx, ry = meters_to_cell()
    expand_map_if_needed(rx, ry)
    rx, ry = meters_to_cell()

    if not (0 <= rx < MAP_W and 0 <= ry < MAP_H):
        return

    # marcar trayectoria
    grid[ry, rx] = TRACE

    # reducir resolución
    mini = mask[::16, ::16]
    mh, mw = mini.shape

    cx = mw // 2
    cy = mh

    # ===============================
    # BASE VECTORIAL 
    # ===============================

    theta_corr = -theta

    fx = math.cos(theta_corr)
    fy = math.sin(theta_corr)

    rx_v = math.sin(theta_corr)
    ry_v = -math.cos(theta_corr)

    for r in range(mh):
        for c in range(mw):

            # coordenadas locales
            lx = cx - c      # derecha
            ly = cy - r      # adelante

            # proyección a mundo
            gx_rel = lx * rx_v + ly * fx
            gy_rel = lx * ry_v + ly * fy

            gx = int(rx + gx_rel)
            gy = int(ry + gy_rel)

            if 0 <= gx < MAP_W and 0 <= gy < MAP_H:

                # no borrar trayectoria
                if grid[gy, gx] == TRACE:
                    continue

                grid[gy, gx] = mini[r, c]