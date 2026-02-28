import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import time

# ===============================
# CONFIGURACIÓN
# ===============================
MODEL_PATH = "lunarModel_rpi5_cpu.tflite"
IMG_PATH = "PCAM5.png"  
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
INPUT_HEIGHT = input_details[0]['shape'][1]  # Altura esperada por el modelo
INPUT_WIDTH = input_details[0]['shape'][2]   # Ancho esperado por el modelo
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
# PREPROCESAMIENTO
# ===============================
# Verificar si la imagen ya tiene el tamaño esperado por el modelo
if h == INPUT_HEIGHT and w == INPUT_WIDTH:
    print(f"✅ La imagen ya tiene el tamaño correcto ({INPUT_WIDTH}x{INPUT_HEIGHT}). Usando directamente.")
    img_resized = img0
else:
    print(f"⚠️ La imagen no tiene el tamaño esperado ({INPUT_WIDTH}x{INPUT_HEIGHT}). Redimensionando...")
    img_resized = cv2.resize(img0, (INPUT_WIDTH, INPUT_HEIGHT))

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
# Obtener máscara (la forma dependerá del modelo)
mask_output = interpreter.get_tensor(output_details[0]['index'])[0]

# Verificar la forma de la salida
print(f"Forma de la máscara de salida: {mask_output.shape}")

# Si la salida tiene 4 dimensiones (como [height, width, num_classes])
if len(mask_output.shape) == 3:
    mask_class = np.argmax(mask_output, axis=-1).astype(np.uint8)
# Si la salida tiene 2 dimensiones (ya es la máscara clasificada)
elif len(mask_output.shape) == 2:
    mask_class = mask_output.astype(np.uint8)
else:
    print(f"⚠️ Forma de salida no esperada: {mask_output.shape}")
    # Intentar manejar otros casos
    if len(mask_output.shape) == 4:  # [1, height, width, classes]
        mask_class = np.argmax(mask_output[0], axis=-1).astype(np.uint8)
    else:
        raise ValueError(f"No se puede procesar la salida con forma {mask_output.shape}")

# Si la imagen original no tenía el tamaño de entrada del modelo,
# redimensionar la máscara al tamaño original
if h != INPUT_HEIGHT or w != INPUT_WIDTH:
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

# Colores para cada clase (ajusta según tus clases reales)
colors = [
    [0, 255, 0],    # Clase 0: ¿Suelo? - Verde
    [0, 0, 255],    # Clase 1: ¿Rocas? - Rojo
    [255, 0, 0],    # Clase 2: ¿Cráteres? - Azul
    [255, 255, 0],  # Clase 3: ¿Otros? - Amarillo
]

# Aplicar color a cada píxel según su clase
num_classes = mask_final.max() + 1
print(f"Número de clases detectadas en la máscara: {num_classes}")

for class_id in range(num_classes):
    if class_id < len(colors):
        overlay[mask_final == class_id] = colors[class_id]
    else:
        # Si hay más clases que colores definidos, usar blanco
        overlay[mask_final == class_id] = [255, 255, 255]

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

# ===============================
# MOSTRAR IMAGEN (opcional, para depuración)
# ===============================
# cv2.imshow("Original", img0)
# cv2.imshow("Segmentación", result)
# cv2.waitKey(0)
# cv2.destroyAllWindows()