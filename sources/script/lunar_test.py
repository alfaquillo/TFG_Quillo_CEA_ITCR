import os
import cv2
import numpy as np
import time
import tensorflow as tf

# ==============================
# CONFIGURACIÓN
# ==============================

MODEL_PATH = "lunarModel_rpi5_cpu.tflite"
IMAGE_DIR = "dataset_test"
SAVE_DIR = "results"

DEBUG = True
SAVE_IMAGES = True

IMG_DATASET_H = 240
IMG_DATASET_W = 320

MODEL_H = 256
MODEL_W = 320

NAV_CLASSES = [0, 1]

FRAMES_PER_DECISION = 5

os.makedirs(SAVE_DIR, exist_ok=True)

# ==============================
# CARGAR MODELO
# ==============================

interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# ==============================
# CARGAR DATASET
# ==============================

image_paths = sorted([
    os.path.join(IMAGE_DIR, x)
    for x in os.listdir(IMAGE_DIR)
    if x.lower().endswith((".jpg", ".png"))
])

print("Imágenes encontradas:", len(image_paths))

# ==============================
# FUNCIONES
# ==============================

def preprocess(img):

    model_img = cv2.resize(img, (MODEL_W, MODEL_H))
    model_img = model_img.astype(np.float32) / 255.0
    model_img = np.expand_dims(model_img, axis=0)

    return model_img


def infer(model_img):

    interpreter.set_tensor(input_details[0]["index"], model_img)
    interpreter.invoke()

    output = interpreter.get_tensor(output_details[0]["index"])[0]

    mask = np.argmax(output, axis=-1)

    mask = cv2.resize(mask.astype(np.uint8),
                      (IMG_DATASET_W, IMG_DATASET_H),
                      interpolation=cv2.INTER_NEAREST)

    return mask


def create_navigation_mask(mask):

    nav = np.isin(mask, NAV_CLASSES).astype(np.uint8)

    return nav


def trapezoid_roi(img_shape):

    h, w = img_shape

    mask = np.zeros((h, w), dtype=np.uint8)

    top_y = int(h * 0.55)
    bottom_y = int(h * 0.95)

    top_left = int(w * 0.40)
    top_right = int(w * 0.60)

    bottom_left = int(w * 0.15)
    bottom_right = int(w * 0.85)

    pts = np.array([[
        (top_left, top_y),
        (top_right, top_y),
        (bottom_right, bottom_y),
        (bottom_left, bottom_y)
    ]], dtype=np.int32)

    cv2.fillPoly(mask, pts, 1)

    return mask


def decide_direction(nav_mask, roi_mask):

    region = nav_mask * roi_mask

    h, w = region.shape

    center = region[:, int(w*0.4):int(w*0.6)]
    left = region[:, :int(w*0.4)]
    right = region[:, int(w*0.6):]

    center_ratio = np.mean(center)
    left_ratio = np.mean(left)
    right_ratio = np.mean(right)

    if center_ratio > 0.20:
        decision = "FORWARD"
    else:
        if left_ratio > right_ratio:
            decision = "LEFT"
        else:
            decision = "RIGHT"

    return decision, center_ratio, left_ratio, right_ratio


def colorize_mask(mask):

    colors = np.array([
        [60,60,60],      # suelo
        [0,255,255],     # small rocks
        [0,0,255],       # large rocks
        [255,200,0]      # sky
    ], dtype=np.uint8)

    return colors[mask]


# ==============================
# BENCHMARK
# ==============================

roi_mask = trapezoid_roi((IMG_DATASET_H, IMG_DATASET_W))

start = time.time()

decision_buffer = []

for idx, path in enumerate(image_paths):

    img = cv2.imread(path)

    model_img = preprocess(img)

    mask = infer(model_img)

    nav_mask = create_navigation_mask(mask)

    decision, c, l, r = decide_direction(nav_mask, roi_mask)

    decision_buffer.append(decision)

    # decisión final cada 5 frames
    if len(decision_buffer) == FRAMES_PER_DECISION:

        final_decision = max(set(decision_buffer), key=decision_buffer.count)

        print(
            f"Frame {idx} | "
            f"center={c:.2f} left={l:.2f} right={r:.2f} | "
            f"DECISION={final_decision}"
        )

        decision_buffer = []

    # ======================
    # DEBUG VISUAL
    # ======================

    if DEBUG:

        color_mask = colorize_mask(mask)

        overlay = cv2.addWeighted(img, 0.6, color_mask, 0.4, 0)

        roi_vis = (roi_mask * 255).astype(np.uint8)
        roi_vis = cv2.cvtColor(roi_vis, cv2.COLOR_GRAY2BGR)

        combined = np.hstack([
            img,
            color_mask,
            overlay
        ])

        cv2.imshow("debug", combined)
        cv2.waitKey(1)

        if SAVE_IMAGES:

            out_path = os.path.join(SAVE_DIR, f"frame_{idx:04d}.png")
            cv2.imwrite(out_path, combined)

end = time.time()

# ==============================
# RESULTADOS
# ==============================

total_time = end - start
fps = len(image_paths) / total_time

print("\n==== RESULTADOS ====")
print("Imágenes:", len(image_paths))
print("Tiempo:", round(total_time,2), "s")
print("FPS:", round(fps,2))
print("ms/frame:", round(1000/fps,2))