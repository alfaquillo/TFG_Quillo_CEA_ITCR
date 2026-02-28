#!/usr/bin/env python3
"""
Script para analizar el stream del Galaxy RVR en modo AP
Muestreo de 1 minuto con estadísticas detalladas
"""

import cv2
import time
import sys
import numpy as np
from collections import deque
from datetime import datetime
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ---
ROVER_IP = "192.168.4.1"  # IP del rover en modo AP
STREAM_URL = f"http://{ROVER_IP}:9000/mjpg"
TIEMPO_MUESTREO = 300  # 1 minuto exacto
# ---------------------

def test_conexion(stream_url):
    """Prueba rápida de conexión"""
    captura = cv2.VideoCapture(stream_url)
    if not captura.isOpened():
        return False
    ret, frame = captura.read()
    captura.release()
    return ret and frame is not None

def analizar_stream_detallado(stream_url, duracion=60):
    """
    Análisis exhaustivo del stream durante 'duracion' segundos
    """
    print(f"\n[INFO] Iniciando análisis de {duracion} segundos...")
    print(f"[INFO] Conectando a {stream_url}")
    
    captura = cv2.VideoCapture(stream_url)
    
    if not captura.isOpened():
        print("[ERROR] No se pudo conectar al stream")
        print("  Posibles causas:")
        print("  - ¿El rover está encendido?")
        print("  - ¿Tu laptop está conectada a la WiFi del rover?")
        print("  - La IP debería ser 192.168.4.1 en modo AP")
        return None
    
    # Buffer para almacenar métricas
    timestamps = []
    intervalos = []  # tiempo entre fotogramas
    tamanos = []     # tamaño aproximado de los fotogramas (basado en compresión)
    fps_inst = []
    
    # Variables de control
    frame_count = 0
    errores = 0
    tiempo_inicio = time.time()
    tiempo_limite = tiempo_inicio + duracion
    
    # Obtener primer fotograma para resolución
    ret, primer_frame = captura.read()
    if not ret:
        print("[ERROR] No se pudo leer el primer fotograma")
        captura.release()
        return None
    
    alto, ancho = primer_frame.shape[:2]
    print(f"[INFO] Resolución detectada: {ancho} x {alto}")
    print(f"[INFO] Iniciando muestreo de {duracion} segundos...")
    print("\n" + "=" * 60)
    
    tiempo_anterior = time.time()
    timestamps.append(tiempo_anterior)
    
    # Barra de progreso simple
    print("Progreso: [", end="", flush=True)
    progreso_anterior = 0
    
    while time.time() < tiempo_limite:
        ret, frame = captura.read()
        tiempo_actual = time.time()
        
        if ret:
            frame_count += 1
            
            # Calcular intervalo
            delta_t = tiempo_actual - tiempo_anterior
            intervalos.append(delta_t)
            
            # Calcular FPS instantáneo
            if delta_t > 0:
                fps_actual = 1.0 / delta_t
                fps_inst.append(fps_actual)
            
            # Estimar tamaño del frame (basado en compresión JPEG)
            # Esto nos da una idea del ancho de banda
            ret_jpg, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret_jpg:
                tamanos.append(len(buffer))
            
            timestamps.append(tiempo_actual)
            tiempo_anterior = tiempo_actual
        else:
            errores += 1
        
        # Actualizar barra de progreso
        progreso_actual = int((time.time() - tiempo_inicio) / duracion * 50)
        if progreso_actual > progreso_anterior:
            print("=" * (progreso_actual - progreso_anterior), end="", flush=True)
            progreso_anterior = progreso_actual
    
    print("] 100%")
    
    tiempo_total = time.time() - tiempo_inicio
    captura.release()
    
    # Calcular estadísticas
    if frame_count == 0:
        print("[ERROR] No se recibió ningún fotograma")
        return None
    
    fps_medio = frame_count / tiempo_total
    
    print("\n" + "=" * 70)
    print("📊 RESULTADOS DEL ANÁLISIS (1 MINUTO)")
    print("=" * 70)
    
    print(f"\n📐 INFORMACIÓN GENERAL:")
    print(f"   • Resolución: {ancho} x {alto}")
    print(f"   • Tiempo real de muestreo: {tiempo_total:.2f} segundos")
    print(f"   • Fotogramas totales: {frame_count}")
    print(f"   • Errores de lectura: {errores}")
    
    print(f"\n📈 ESTADÍSTICAS DE FPS:")
    print(f"   • Media: {fps_medio:.2f} fps")
    if fps_inst:
        print(f"   • Máximo: {max(fps_inst):.2f} fps")
        print(f"   • Mínimo: {min(fps_inst):.2f} fps")
        print(f"   • Mediana: {np.median(fps_inst):.2f} fps")
        print(f"   • Desviación estándar: {np.std(fps_inst):.2f} fps")
        
        # Percentiles
        p10 = np.percentile(fps_inst, 10)
        p90 = np.percentile(fps_inst, 90)
        print(f"   • Percentil 10: {p10:.2f} fps (el 10% del tiempo por debajo de esto)")
        print(f"   • Percentil 90: {p90:.2f} fps (el 90% del tiempo por debajo de esto)")
        
        # Rango intercuartil
        q1 = np.percentile(fps_inst, 25)
        q3 = np.percentile(fps_inst, 75)
        print(f"   • Rango intercuartil (Q1-Q3): {q1:.2f} - {q3:.2f} fps")
    
    print(f"\n⏱️  ESTADÍSTICAS DE INTERVALOS:")
    intervalos_ms = np.array(intervalos) * 1000
    print(f"   • Media: {np.mean(intervalos_ms):.1f} ms")
    print(f"   • Máximo: {np.max(intervalos_ms):.1f} ms")
    print(f"   • Mínimo: {np.min(intervalos_ms):.1f} ms")
    
    if tamanos:
        print(f"\n💾 ESTIMACIÓN DE ANCHO DE BANDA:")
        tamanos_kb = np.array(tamanos) / 1024
        ancho_banda_medio = np.mean(tamanos_kb) * fps_medio  # KB/s
        ancho_banda_max = np.max(tamanos_kb) * max(fps_inst) if fps_inst else 0
        
        print(f"   • Tamaño medio por frame: {np.mean(tamanos_kb):.1f} KB")
        print(f"   • Ancho de banda medio: {ancho_banda_medio:.1f} KB/s ({ancho_banda_medio*8:.1f} Kbps)")
        print(f"   • Pico estimado: {ancho_banda_max:.1f} KB/s")
    
    # Análisis de estabilidad
    print(f"\n📋 ANÁLISIS DE ESTABILIDAD:")
    if fps_inst:
        variacion = (np.std(fps_inst) / fps_medio) * 100
        if variacion < 15:
            print(f"   ✅ MUY ESTABLE: Variación del {variacion:.1f}%")
        elif variacion < 25:
            print(f"   ⚠️  MODERADAMENTE VARIABLE: Variación del {variacion:.1f}%")
            print(f"      Tus mediciones de 3-6 fps son consistentes con esto")
        else:
            print(f"   ❌ MUY VARIABLE: Variación del {variacion:.1f}%")
            print(f"      El stream es inestable, revisa interferencias")
    
    # Comparación con tu observación
    print(f"\n🔍 COMPARACIÓN CON TU OBSERVACIÓN:")
    print(f"   • Tú observaste: 3-6 fps")
    print(f"   • El análisis muestra: {fps_medio:.1f} fps de media")
    if fps_inst:
        if min(fps_inst) <= 3 and max(fps_inst) >= 6:
            print("   ✅ Coincide exactamente con tu observación")
        else:
            print(f"   📊 Rango real: {min(fps_inst):.1f} - {max(fps_inst):.1f} fps")
    
    # Recomendaciones específicas para modo AP
    print(f"\n💡 RECOMENDACIONES PARA MODO AP:")
    print("   El modo AP es más estable pero limitado en ancho de banda.")
    print("   Para mejorar los FPS puedes:")
    print("   1. Reducir la resolución a 320x240 (QVGA)")
    print("   2. Reducir la calidad JPEG (menos calidad = menos datos)")
    print("   3. Cerrar otras aplicaciones que usen WiFi")
    print("   4. Acercar la laptop al rover (la señal WiFi es directa)")
    
    # Generar gráficas
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'Análisis de Stream Galaxy RVR - 1 minuto', fontsize=16)
        
        # Gráfica 1: FPS en el tiempo
        ax1 = axes[0, 0]
        tiempos_rel = [(t - timestamps[0]) for t in timestamps[1:]]
        ax1.plot(tiempos_rel, fps_inst, 'b-', alpha=0.7, linewidth=0.5)
        ax1.axhline(y=fps_medio, color='r', linestyle='--', label=f'Media: {fps_medio:.1f} fps')
        ax1.fill_between(tiempos_rel, fps_inst, fps_medio, alpha=0.1, color='red')
        ax1.set_xlabel('Tiempo (segundos)')
        ax1.set_ylabel('FPS instantáneos')
        ax1.set_title('Evolución de FPS en el tiempo')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Gráfica 2: Histograma de FPS
        ax2 = axes[0, 1]
        ax2.hist(fps_inst, bins=20, alpha=0.7, color='blue', edgecolor='black')
        ax2.axvline(x=fps_medio, color='r', linestyle='--', label=f'Media: {fps_medio:.1f}')
        ax2.axvline(x=np.median(fps_inst), color='g', linestyle='--', label=f'Mediana: {np.median(fps_inst):.1f}')
        ax2.set_xlabel('FPS')
        ax2.set_ylabel('Frecuencia')
        ax2.set_title('Distribución de FPS')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Gráfica 3: Intervalos entre frames
        ax3 = axes[1, 0]
        ax3.hist(intervalos_ms, bins=30, alpha=0.7, color='green', edgecolor='black')
        ax3.axvline(x=np.mean(intervalos_ms), color='r', linestyle='--', 
                   label=f'Media: {np.mean(intervalos_ms):.1f} ms')
        ax3.set_xlabel('Intervalo entre frames (ms)')
        ax3.set_ylabel('Frecuencia')
        ax3.set_title('Distribución de intervalos')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Gráfica 4: Acumulado de frames
        ax4 = axes[1, 1]
        frames_acumulados = np.cumsum([1] * frame_count)
        ax4.plot(tiempos_rel, frames_acumulados, 'purple', linewidth=1)
        ax4.set_xlabel('Tiempo (segundos)')
        ax4.set_ylabel('Frames acumulados')
        ax4.set_title('Frames recibidos en el tiempo')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Guardar gráfica
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analisis_rover_{timestamp}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"\n   📈 Gráfica guardada como: {filename}")
        plt.show()
        
    except Exception as e:
        print(f"\n   ⚠️ No se pudo generar la gráfica: {e}")
    
    return {
        'fps_medio': fps_medio,
        'fps_min': min(fps_inst) if fps_inst else 0,
        'fps_max': max(fps_inst) if fps_inst else 0,
        'fps_std': np.std(fps_inst) if fps_inst else 0,
        'frame_count': frame_count,
        'resolucion': (ancho, alto)
    }

def main():
    print("=" * 70)
    print("🔍 ANALIZADOR DE STREAM - GALAXY RVR (MODO AP)")
    print("=" * 70)
    print("\nEste script analizará el stream de video durante 1 MINUTO")
    print("para verificar la variabilidad que has observado (3-6 fps).")
    
    # Prueba rápida de conexión
    print("\n[TEST] Verificando conexión con el rover...")
    if test_conexion(STREAM_URL):
        print("[TEST] ✅ Conexión exitosa")
    else:
        print("[TEST] ❌ No se pudo conectar")
        print("\n¿Estás conectado a la WiFi del rover?")
        print("La IP debería ser 192.168.4.1")
        respuesta = input("\n¿Quieres intentar igualmente? (s/N): ")
        if respuesta.lower() != 's':
            sys.exit(1)
    
    input("\nPresiona ENTER para comenzar el análisis de 1 minuto...")
    
    resultados = analizar_stream_detallado(STREAM_URL, duracion=TIEMPO_MUESTREO)
    
    if resultados:
        print("\n" + "=" * 70)
        print("✅ ANÁLISIS COMPLETADO")
        print("=" * 70)
        print(f"\n📝 RESUMEN FINAL:")
        print(f"   • Resolución: {resultados['resolucion'][0]}x{resultados['resolucion'][1]}")
        print(f"   • FPS medio: {resultados['fps_medio']:.2f}")
        print(f"   • Rango: {resultados['fps_min']:.2f} - {resultados['fps_max']:.2f} fps")
        print(f"   • Frames totales: {resultados['frame_count']}")
        
        if resultados['fps_medio'] < 10:
            print("\n⚠️  Los FPS son bajos para video fluido.")
            print("   Considera reducir la resolución del rover.")
    else:
        print("\n❌ No se pudo completar el análisis")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Análisis interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
        