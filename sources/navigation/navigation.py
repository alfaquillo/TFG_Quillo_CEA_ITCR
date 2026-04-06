import numpy as np

def decide_direction(nav_mask, roi_mask):

    region = nav_mask * roi_mask
    h, w = region.shape

    left   = region[:, :int(w*0.4)]
    center = region[:, int(w*0.4):int(w*0.6)]
    right  = region[:, int(w*0.6):]

    near_h = int(h*0.6)

    center_ratio = 0.7*np.mean(center[near_h:, :]) + 0.3*np.mean(center[:near_h, :])
    left_ratio   = np.mean(left)
    right_ratio  = np.mean(right)

    MIN_FORWARD = 0.18
    DELTA_SIDE  = 0.05
    DELTA_CENTER = 0.06

    best_side = max(left_ratio, right_ratio)
    side_diff = abs(left_ratio - right_ratio)

    if center_ratio > MIN_FORWARD and (best_side - center_ratio) < DELTA_CENTER:
        decision = "ADELANTE"
    elif side_diff > DELTA_SIDE:
        decision = "IZQUIERDA" if left_ratio > right_ratio else "DERECHA"
    else:
        decision = "ADELANTE"

    return decision, center_ratio, left_ratio, right_ratio