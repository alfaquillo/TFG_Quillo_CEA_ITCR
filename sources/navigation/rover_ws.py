import asyncio
import websockets
import json

# ======================
# CONFIG
# ======================
ROVER_URI = "ws://10.20.40.150:8765"

VEL_MAX = 5
CMD_TIME = 250   # ms

# ======================
# MAPEO SLAM → MOTORES
# ======================
def decision_to_motors(decision):
    

    if decision == "ADELANTE":
        izq = VEL_MAX
        der = VEL_MAX

    elif decision == "IZQUIERDA":
        izq = int(VEL_MAX * 0.2)
        der = VEL_MAX*1.5

    elif decision == "DERECHA":
        izq = VEL_MAX*1.5
        der = int(VEL_MAX * 0.2)

    else:
        izq = 0
        der = 0

    return izq, der


# ======================
# CLIENTE WEBSOCKET
# ======================
class RoverClient:

    def __init__(self, uri=ROVER_URI):
        self.uri = uri
        self.ws = None

    async def connect(self):
        self.ws = await websockets.connect(
            self.uri,
            ping_interval=None,
            ping_timeout=None
        )
        print("Conectado al rover")

    async def send_command(self, decision):

        izq, der = decision_to_motors(decision)

        cmd = {
            "K": izq,
            "Q": der*1.3,
            "D": 90,
            "M": 0,
            "E": 0,
            "F": 0,
            "duracion_ms": CMD_TIME
        }

        await self.ws.send(json.dumps(cmd))

        try:
            await asyncio.wait_for(self.ws.recv(), timeout=1.0)
        except asyncio.TimeoutError:
            print("ACK tardío")

    async def close(self):
        if self.ws:
            await self.ws.close()