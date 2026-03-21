import os
import cv2
import numpy as np
import time

# ==============================
# IMPORT TFLITE (PC / RPI)
# ==============================

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow as tflite


# ==============================
# CONFIGURACIÓN
# ==============================

#MODEL_PATH = "lunar_rpi5_int8.tflite" #RPI
MODEL_PATH = "lunar_rpi5_float16.tflite" #INTELCPU
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

os.makedirs(SAVE_DIR, exist_ok=True)

USE_TRAPEZOID = True


# ==============================
# CARGAR MODELO
# ==============================

interpreter = tflite.Interpreter(
    model_path=MODEL_PATH,
    num_threads=8   # recomendado para RPi5
)

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

    img = cv2.resize(img, (MODEL_W, MODEL_H))

    input_dtype = input_details[0]["dtype"]

    if input_dtype == np.uint8:
        img = img.astype(np.uint8)

    else:  # float32
        img = img.astype(np.float32) / 255.0

    img = np.expand_dims(img, 0)

    return img


def infer(model_img):

    interpreter.set_tensor(input_details[0]["index"], model_img)
    interpreter.invoke()

    output = interpreter.get_tensor(output_details[0]["index"])[0]

    mask = np.argmax(output, axis=-1)

    mask = cv2.resize(
        mask.astype(np.uint8),
        (IMG_DATASET_W, IMG_DATASET_H),
        interpolation=cv2.INTER_NEAREST
    )

    return mask


def create_navigation_mask(mask):

    nav = np.isin(mask, NAV_CLASSES).astype(np.uint8)

    return nav


def trapezoid_roi(img_shape):

    h, w = img_shape

    if not USE_TRAPEZOID:
        full = np.ones((h, w), dtype=np.uint8)
        return full, None

    mask = np.zeros((h, w), dtype=np.uint8)

    top_y = int(h * 0.10)      # borde superior
    bottom_y = int(h * 0.50)   # borde inferior

    top_left = int(w * 0.15)   # ancho bordes superiores
    top_right = int(w * 0.85)

    bottom_left = int(w * 0.02)  # ancho bordes inferiores
    bottom_right = int(w * 0.98)

    pts = np.array([
        (top_left, top_y),
        (top_right, top_y),
        (bottom_right, bottom_y),
        (bottom_left, bottom_y)
    ], dtype=np.int32)

    cv2.fillPoly(
        img=mask,
        pts=[pts.astype(np.int32)],
        color=(1,)
    )

    #cv2.fillPoly(mask, [pts], 1)

    return mask, pts


def decide_direction(nav_mask, roi_mask):

    region = nav_mask * roi_mask
    h, w = region.shape

    left   = region[:, :int(w*0.4)]
    center = region[:, int(w*0.4):int(w*0.6)]
    right  = region[:, int(w*0.6):]

    near_h = int(h*0.6)

    center_near = center[near_h:, :]
    center_far  = center[:near_h, :]

    center_ratio = 0.7*np.mean(center_near) + 0.3*np.mean(center_far)
    left_ratio   = np.mean(left)
    right_ratio  = np.mean(right)


    MIN_FORWARD = 0.18
    DELTA_SIDE  = 0.05     # diferencia mínima real entre lados
    DELTA_CENTER = 0.06    # centro claramente peor para evitar avanzar

    best_side = max(left_ratio, right_ratio)
    side_diff = abs(left_ratio - right_ratio)

    #  avanzar si centro es suficiente y no es claramente peor
    if center_ratio > MIN_FORWARD and (best_side - center_ratio) < DELTA_CENTER:
        decision = "ADELANTE"

    #  girar solo si hay diferencia REAL entre lados
    elif side_diff > DELTA_SIDE:
        if left_ratio > right_ratio:
            decision = "IZQUIERDA"
        else:
            decision = "DERECHA"

    # empate lateral → avanzar
    else:
        decision = "ADELANTE"

    return decision, center_ratio, left_ratio, right_ratio

def colorize_mask(mask):

    colors = np.array([
        [60, 60, 60],     # class 0
        [0, 255, 255],    # class 1
        [0, 0, 255],      # class 2
        [255, 200, 0],    # class 3
        [0, 255, 0]       # class 4
    ], dtype=np.uint8)

    return colors[mask]


# ==============================
# BENCHMARK
# ==============================

roi_mask, roi_pts = trapezoid_roi((IMG_DATASET_H, IMG_DATASET_W))

start = time.time()

decision_buffer = []

for idx, path in enumerate(image_paths):

    img = cv2.imread(path)

    model_img = preprocess(img)

    mask = infer(model_img)

    print("Clases detectadas:", np.unique(mask))

    nav_mask = create_navigation_mask(mask)

    decision, c, l, r = decide_direction(nav_mask, roi_mask)

    decision_buffer.append(decision)

    # decisión final cada N frames
    if len(decision_buffer) == FRAMES_PER_DECISION:

        final_decision = max(set(decision_buffer), key=decision_buffer.count)

        print(
            f"Frame {idx} | "
            f"centro={c:.2f} izquierda={l:.2f} derecha={r:.2f} | "
            f"DECISION={final_decision}"
        )

        decision_buffer = []


    # ======================
    # DEBUG VISUAL
    # ======================
    if DEBUG:

        color_mask = colorize_mask(mask)

        overlay = cv2.addWeighted(img, 0.6, color_mask, 0.4, 0)

        if roi_pts is not None:
            cv2.polylines(
                overlay,
                [roi_pts],
                isClosed=True,
                color=(255,0,255),   # magenta
                thickness=2
            )

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