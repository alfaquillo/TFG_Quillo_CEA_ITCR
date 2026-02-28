import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import time

# ===============================
# CONFIGURACIÓN
# ===============================
MODEL_PATH = "lunarModel_rpi5_cpu.tflite"
IMG_PATH = "TCAM3.png"  
CONF_THRES = 0.5

# ===============================
# CARGAR MODELO
# ===============================
print("Cargando modelo...")
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Obtener tamaño que espera el modelo
EXPECTED_SIZE = input_details[0]['shape'][1]  # Debería ser 256
print(f"Modelo espera entrada: {input_details[0]['shape']}")
print(f"Salidas del modelo lunar: {len(output_details)}")
print(f"Forma de salida: {output_details[0]['shape']}")

# ===============================
# CARGAR IMAGEN
# ===============================
t0 = time.perf_counter()

img0 = cv2.imread(IMG_PATH)
if img0 is None:
    raise FileNotFoundError(f"❌ No se pudo cargar la imagen: {IMG_PATH}")

h, w = img0.shape[:2]
print(f"Imagen cargada: {w}x{h}")

# ===============================
# PREPROCESAMIENTO INTELIGENTE
# ===============================
if h == EXPECTED_SIZE and w == EXPECTED_SIZE:
    print("✅ La imagen ya tiene el tamaño correcto. Usando directamente.")
    img_resized = img0
else:
    print(f"⚠️ La imagen no tiene el tamaño esperado ({EXPECTED_SIZE}x{EXPECTED_SIZE}). Redimensionando...")
    img_resized = cv2.resize(img0, (EXPECTED_SIZE, EXPECTED_SIZE))

# Normalizar (igual que en entrenamiento)
img_input = img_resized.astype(np.float32) / 255.0
img_input = np.expand_dims(img_input, axis=0)

t1 = time.perf_counter()

# ===============================
# INFERENCIA
# ===============================
interpreter.set_tensor(input_details[0]['index'], img_input)
interpreter.invoke()

t2 = time.perf_counter()

# ===============================
# POSTPROCESO
# ===============================
# Obtener máscara (shape: [1, 256, 256, 4])
mask_output = interpreter.get_tensor(output_details[0]['index'])[0]

# Tomar la clase con mayor probabilidad
mask_class = np.argmax(mask_output, axis=-1).astype(np.uint8)

# Si la imagen original no era 256x256, redimensionar la máscara al tamaño original
if h != EXPECTED_SIZE or w != EXPECTED_SIZE:
    print(f"Redimensionando máscara al tamaño original {w}x{h}")
    mask_final = cv2.resize(mask_class, (w, h), interpolation=cv2.INTER_NEAREST)
else:
    mask_final = mask_class

t3 = time.perf_counter()

# ===============================
# VISUALIZACIÓN
# ===============================
# Crear overlay coloreado
result = img0.copy()
overlay = np.zeros_like(img0)

# Colores para cada clase
colors = [
    [0, 255, 0],    # Clase 0: ¿Suelo? - Verde
    [0, 0, 255],    # Clase 1: ¿Rocas? - Rojo
    [255, 0, 0],    # Clase 2: ¿Cráteres? - Azul
    [255, 255, 0],  # Clase 3: ¿Otros? - Amarillo
]

# Aplicar color a cada píxel según su clase
for class_id in range(mask_final.max() + 1):
    if class_id < len(colors):
        overlay[mask_final == class_id] = colors[class_id]

# Mezclar imagen original con overlay
alpha = 0.5
result = cv2.addWeighted(img0, 1-alpha, overlay, alpha, 0)

# ===============================
# GUARDAR RESULTADOS
# ===============================
output_name = f"segmented_{IMG_PATH}"
cv2.imwrite(output_name, result)
print(f"✅ Resultado guardado en {output_name}")

# ===============================
# MOSTRAR ESTADÍSTICAS
# ===============================
print("\n==== ESTADÍSTICAS DE SEGMENTACIÓN ====")
unique, counts = np.unique(mask_final, return_counts=True)
total_pixels = mask_final.size

class_names = ["Suelo", "Rocas", "Cráteres", "Otros"]
for class_id, count in zip(unique, counts):
    percentage = (count / total_pixels) * 100
    class_name = class_names[class_id] if class_id < len(class_names) else f"Clase {class_id}"
    color = colors[class_id] if class_id < len(colors) else [255, 255, 255]
    print(f"{class_name}: {percentage:.1f}% del área")

# ===============================
# TIEMPOS
# ===============================
print("\n==== TIEMPOS ====")
print(f"Carga y preproceso: {(t1-t0)*1000:.2f} ms")
print(f"Inferencia: {(t2-t1)*1000:.2f} ms")
print(f"Postproceso: {(t3-t2)*1000:.2f} ms")
print(f"Total: {(t3-t0)*1000:.2f} ms")

