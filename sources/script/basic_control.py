import asyncio
import json
import cv2
import websockets
import threading

ROVER_URI = "ws://192.168.4.1:8765"
CAM_URI = "http://192.168.4.1:9000/mjpg"

# =====================
# Comando compartido
# =====================
cmd_actual = {"K": 10, "Q": 10, "D": 90, "M": 0, "E": 0, "F": 0, "duracion_ms": 500}
ack_event = asyncio.Event()  # Señal para sincronizar envío

# =====================
# Visualización de la cámara
# =====================
def ver_camara():
    cap = cv2.VideoCapture(CAM_URI, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("No se pudo abrir la cámara")
        return

    cv2.namedWindow("Cámara Rover", cv2.WINDOW_NORMAL)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("No se recibió frame")
            break
        frame = cv2.flip(frame, -1)
        cv2.imshow("Cámara Rover", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# =====================
# Loop de envío de comandos sincronizado
# =====================
async def enviar_loop(ws):
    global cmd_actual
    while True:
        await ack_event.wait()           # Espera que el rover envíe un mensaje
        ack_event.clear()
        try:
            await ws.send(json.dumps(cmd_actual))
        except websockets.ConnectionClosed:
            print("Conexión cerrada durante el envío")
            break

# =====================
# Loop de recepción de mensajes
# =====================
async def recibir_loop(ws):
    global ack_event
    while True:
        try:
            resp = await ws.recv()
            print("Rover dice:", resp)
            ack_event.set()  # Señal para enviar el próximo comando
        except websockets.ConnectionClosed:
            print("Conexión cerrada por el rover")
            break

# =====================
# Función principal
# =====================
async def mover_rover_loop():
    try:
        async with websockets.connect(ROVER_URI, ping_interval=5, ping_timeout=10) as ws:
            print("Conectado al rover")
            # Inicializamos evento para enviar el primer comando
            ack_event.set()
            await asyncio.gather(
                enviar_loop(ws),
                recibir_loop(ws)
            )
    except websockets.ConnectionClosedError as e:
        print("Error de conexión:", e)

# =====================
# Main
# =====================
if __name__ == "__main__":
    # Cámara en thread independiente
    cam_thread = threading.Thread(target=ver_camara, daemon=True)
    cam_thread.start()

    # Loop principal de movimiento
    try:
        asyncio.run(mover_rover_loop())
    except KeyboardInterrupt:
        print("Programa interrumpido por el usuario")