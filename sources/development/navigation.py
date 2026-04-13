import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import time

MODEL_PATH = "yolo/yolo26n-seg_saved_model/yolo26n-seg_float16.tflite"
IMG_PATH = "TCAM22.png"
IMG_SIZE = 320
CONF_THRES = 0.5

# ===============================
# CARGAR MODELO
# ===============================
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# ===============================
# PREPROCESAMIENTO
# ===============================
t0 = time.perf_counter() #inicio de cuenta de tiempo

img0 = cv2.imread(IMG_PATH)
t1 = time.perf_counter() #contador de captura

img = cv2.resize(img0, (IMG_SIZE, IMG_SIZE))
img_input = img.astype(np.float32) / 255.0
img_input = np.expand_dims(img_input, axis=0)
t2 = time.perf_counter() #contador de preprocesamiento

# ===============================
# WARM-UP
# ===============================
interpreter.set_tensor(input_details[0]['index'], img_input)
interpreter.invoke()

# ===============================
# INFERENCIA 
# ===============================
t_inf_start = time.perf_counter()

interpreter.set_tensor(input_details[0]['index'], img_input)
interpreter.invoke()

t3 = time.perf_counter() #contador de inferencia

# ===============================
# POSTPROCESO
# ===============================
pred = interpreter.get_tensor(output_details[0]['index'])[0]
protos = interpreter.get_tensor(output_details[1]['index'])[0]

boxes = pred[:, :4]
conf = pred[:, 4]

num_classes = pred.shape[1] - 4 - 1 - 32
class_scores = pred[:, 5:5+num_classes]
class_ids = np.argmax(class_scores, axis=1)

mask_coeffs = pred[:, -32:]

valid = conf > CONF_THRES
boxes = boxes[valid]
conf = conf[valid]
class_ids = class_ids[valid]
mask_coeffs = mask_coeffs[valid]

result = img.copy()

for i in range(len(boxes)):
    coeff = mask_coeffs[i]

    mask = np.dot(protos.reshape(-1, 32), coeff)
    mask = mask.reshape(80, 80)
    mask = 1 / (1 + np.exp(-mask))
    mask = cv2.resize(mask, (IMG_SIZE, IMG_SIZE))

    mask_binary = mask > 0.5
    color = np.random.randint(0, 255, size=3)

    result[mask_binary] = result[mask_binary] * 0.5 + color * 0.5

t4 = time.perf_counter() #contador de postprocesamiento

# =============================== 
# # GUARDAR RESULTADO # 
# =============================== 
cv2.imwrite("debug_segmented.jpg", result.astype(np.uint8)) 
print("Saved debug_segmented.jpg")

# ===============================
# PERFIL FINAL
# ===============================
total_time = (
    (t1 - t0) +
    (t2 - t1) +
    (t3 - t_inf_start) +
    (t4 - t3)
)

print("\n==== PERFIL DE TIEMPOS ====")
print(f"Captura: {(t1-t0)*1000:.2f} ms")
print(f"Preproceso: {(t2-t1)*1000:.2f} ms")
print(f"Inferencia: {(t3-t_inf_start)*1000:.2f} ms")
print(f"Postproceso: {(t4-t3)*1000:.2f} ms")
print(f"Total pipeline: {total_time*1000:.2f} ms")
print(f"FPS teórico (1 imagen): {1/total_time:.2f}")


print("\n==== FPS PROMEDIO REAL ====")

num_runs = 30

start_loop = time.perf_counter()

for _ in range(num_runs):
    interpreter.set_tensor(input_details[0]['index'], img_input)
    interpreter.invoke()

end_loop = time.perf_counter()

total_loop_time = end_loop - start_loop
fps_real = num_runs / total_loop_time

print(f"FPS promedio inferencia: {fps_real:.2f}")


