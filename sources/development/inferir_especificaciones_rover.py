#!/usr/bin/env python3
"""
Analizador genérico de stream MJPEG/HTTP.
Configuración interna editable.
"""

import cv2
import time
import sys
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt


# ==========================
# CONFIGURACIÓN EDITABLE
# ==========================
#STREAM_IP = "192.168.4.1"  #AP MODE
STREAM_IP = "10.20.40.111"  #STA MODE
STREAM_PORT = 9000
STREAM_PATH = "mjpg"
TIEMPO_MUESTREO = 60  # segundos
# ==========================


STREAM_URL = f"http://{STREAM_IP}:{STREAM_PORT}/{STREAM_PATH}"


def test_conexion(stream_url):
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        return False
    ret, frame = cap.read()
    cap.release()
    return ret and frame is not None


def analizar_stream(stream_url, duracion=60):
    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print("No se pudo abrir el stream")
        return None

    timestamps = []
    intervalos = []
    tamanos = []
    fps_inst = []

    frame_count = 0
    errores = 0

    t_inicio = time.time()
    t_limite = t_inicio + duracion

    ret, frame = cap.read()
    if not ret:
        cap.release()
        print("No se pudo leer el primer frame")
        return None

    alto, ancho = frame.shape[:2]

    t_anterior = time.time()
    timestamps.append(t_anterior)

    while time.time() < t_limite:
        ret, frame = cap.read()
        t_actual = time.time()

        if ret:
            frame_count += 1

            delta_t = t_actual - t_anterior
            intervalos.append(delta_t)

            if delta_t > 0:
                fps_inst.append(1.0 / delta_t)

            ret_jpg, buffer = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
            )
            if ret_jpg:
                tamanos.append(len(buffer))

            timestamps.append(t_actual)
            t_anterior = t_actual
        else:
            errores += 1

    t_total = time.time() - t_inicio
    cap.release()

    if frame_count == 0:
        print("No se recibieron frames")
        return None

    fps_medio = frame_count / t_total
    intervalos_ms = np.array(intervalos) * 1000

    resultados = {
        "url": stream_url,
        "resolucion": (ancho, alto),
        "frames": frame_count,
        "errores": errores,
        "tiempo_real": t_total,
        "fps_medio": fps_medio,
        "fps_min": min(fps_inst) if fps_inst else 0,
        "fps_max": max(fps_inst) if fps_inst else 0,
        "fps_std": np.std(fps_inst) if fps_inst else 0,
        "intervalo_medio_ms": np.mean(intervalos_ms) if len(intervalos_ms) else 0,
        "tam_frame_kb": np.mean(np.array(tamanos) / 1024) if tamanos else 0,
    }

    generar_graficas(
        timestamps,
        fps_inst,
        intervalos_ms,
        frame_count,
        fps_medio,
    )

    return resultados


def generar_graficas(timestamps, fps_inst, intervalos_ms, frame_count, fps_medio):
    if not fps_inst:
        return

    tiempos_rel = [(t - timestamps[0]) for t in timestamps[1:]]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Análisis de Stream", fontsize=16)

    axes[0, 0].plot(tiempos_rel, fps_inst, linewidth=0.7)
    axes[0, 0].axhline(y=fps_medio, linestyle="--")
    axes[0, 0].set_title("FPS vs Tiempo")

    axes[0, 1].hist(fps_inst, bins=20)
    axes[0, 1].set_title("Distribución FPS")

    axes[1, 0].hist(intervalos_ms, bins=30)
    axes[1, 0].set_title("Intervalo entre frames (ms)")

    frames_acum = np.cumsum([1] * frame_count)
    axes[1, 1].plot(tiempos_rel, frames_acum)
    axes[1, 1].set_title("Frames acumulados")

    plt.tight_layout()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"stream_analysis_{timestamp}.png"
    plt.savefig(filename, dpi=150)

    print(f"Gráfica guardada: {filename}")
    plt.show()


def main():
    print(f"Stream URL: {STREAM_URL}")
    print(f"Duración: {TIEMPO_MUESTREO} s")

    if not test_conexion(STREAM_URL):
        print("Fallo en prueba de conexión")
        sys.exit(1)

    resultados = analizar_stream(STREAM_URL, TIEMPO_MUESTREO)

    if resultados:
        print("\nResumen:")
        for k, v in resultados.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()