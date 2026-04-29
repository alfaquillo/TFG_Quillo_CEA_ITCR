import cv2
import asyncio
import websockets
import json
import time

ROVER_URI = "ws://192.168.4.1:8765"
CAM_URI = "http://192.168.4.1:9000/mjpg"

VEL_MAX = 15
CMD_TIME = 700        
SEND_INTERVAL = 0.40      
KEY_TIMEOUT = 0.18        

keys = set()
key_times = {}
ultimo_envio = 0

# ======================
# MEZCLA DIFERENCIAL TANQUE
# ======================
def calcular_motores():
    avance = 0
    giro = 0

    if ord('w') in keys: avance = 1
    if ord('s') in keys: avance = -1
    if ord('a') in keys: giro = -1
    if ord('d') in keys: giro = 1

    # si no hay avance, permitir giro leve en sitio
    if avance == 0 and giro != 0:
        izq = giro * VEL_MAX * 0.4
        der =  -giro * VEL_MAX * 0.4
        return int(izq), int(der)

    # giro suave tipo vehículo
    giro_factor = 0.4 * giro  # qué tan cerrada la curva

    izq = avance * VEL_MAX * (1 - giro_factor)
    der = avance * VEL_MAX * (1 + giro_factor)

    return int(izq), int(der)

# ======================
# LOOP PRINCIPAL
# ======================
async def main():

    global ultimo_envio

    cap = cv2.VideoCapture(CAM_URI)
    if not cap.isOpened():
        print("No se pudo abrir cámara")
        return

    async with websockets.connect(
        ROVER_URI,
        ping_interval=None,
        ping_timeout=None
    ) as ws:

        print("Modo manual limitado ~2.5 Hz")
        print("WASD mover | Espacio frenar | Q salir")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Sin frame")
                break
            
            cv2.imshow("Rover Cam", frame)

            key = cv2.waitKey(1) & 0xFF

            # registrar pulsación
            if key != 255:
                keys.add(key)
                key_times[key] = time.time()

            # limpiar teclas expiradas (simular release)
            ahora = time.time()
            for k in list(keys):
                if ahora - key_times.get(k, 0) > KEY_TIMEOUT:
                    keys.discard(k)

            # freno inmediato
            if key == ord(' '):
                keys.clear()

            if key == ord('q'):
                break

            # limitar frecuencia de envío
            if ahora - ultimo_envio < SEND_INTERVAL:
                continue

            ultimo_envio = ahora

            izq, der = calcular_motores()

            cmd = {
                "K": izq,
                "Q": der*1.3,
                "M": 0,
                "E": 0,
                "F": 0,
                "duracion_ms": CMD_TIME
            }

            await ws.send(json.dumps(cmd))

            try:
                await asyncio.wait_for(ws.recv(), timeout=1.0)
            except asyncio.TimeoutError:
                print(" ACK tardío → posible saturación ESP32/Serial")

        cap.release()
        cv2.destroyAllWindows()

asyncio.run(main())