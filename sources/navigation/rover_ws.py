import asyncio
import websockets
import json

from config import WS_URI
from sensors import Sensors
from navigation import decide_direction

VEL_MAX = 5
CMD_TIME = 400
bias_d = 2.3
bias_i = 1
OVERRIDE_CYCLES = 3


def decision_to_motors(decision):

    if decision.startswith("sens_"):
        decision = decision.replace("sens_", "")
    elif decision.startswith("nav_"):
        decision = decision.replace("nav_", "")

    if decision == "ADELANTE":
        return VEL_MAX, VEL_MAX

    elif decision == "IZQUIERDA":
        return VEL_MAX * 0.8, VEL_MAX * 1.5

    elif decision == "DERECHA":
        return VEL_MAX * 1.5, VEL_MAX * 0.8

    elif decision == "RETROCEDER":
        return -VEL_MAX, -VEL_MAX

    return 0, 0


class RoverClient:

    def __init__(self, uri=WS_URI):
        self.uri = uri
        self.ws = None

        self.sensors = Sensors()

        self.last_override = "LIBRE"
        self.override_timer = 0

        self.current_command = "nav_ADELANTE"
        self.send_interval = 0.08  # 80 ms

    async def connect(self):
        self.ws = await websockets.connect(
            self.uri,
            ping_interval=None,
            ping_timeout=None
        )
        print("Conectado al rover")

        # servo inicial
        await self.ws.send(json.dumps({
                "K": 0,
                "Q": 0,
                "D": 90,
                "M": 1,
                "E": 0,
                "F": 0,
                "duracion_ms": 1
            }))

        asyncio.create_task(self.ping_loop())
        asyncio.create_task(self.command_stream())
        asyncio.create_task(self.receiver_loop())


    #-----------
    # Ping loop
    #-----------

    async def ping_loop(self):
        while True:
            try:
                await self.ws.send(json.dumps({"ping": 1}))
                await asyncio.sleep(0.5)  
            except Exception as e:
                print("Error ping:", e)
                await asyncio.sleep(0.5)

    # ----------------------
    # RECEPCIÓN (sensores)
    # ----------------------
    async def receiver_loop(self):
        while True:
            try:
                message = await self.ws.recv()

                if not message:
                    continue

                if isinstance(message, bytes):
                    continue

                message = message.strip()

                if not message:
                    continue

                try:
                    data = json.loads(message)
                except:
                    continue  # ← ignorar basura sin log spam

                self.sensors.update(data)

            except Exception as e:
                print("Error RX:", e)
                await asyncio.sleep(0.1)

    # ----------------------
    # DECISIÓN FINAL
    # ----------------------
    def compute_decision(self, nav_mask, roi_mask):

        sens_decision = self.sensors.decide_avoidance()

        if sens_decision != "LIBRE":
            self.last_override = sens_decision
            self.override_timer = OVERRIDE_CYCLES

        if self.override_timer > 0:
            self.override_timer -= 1
            return f"sens_{self.last_override}"

        nav_decision, *_ = decide_direction(nav_mask, roi_mask)
        return f"nav_{nav_decision}"

    # ----------------------
    # ENVÍO
    # ----------------------
    async def send_command(self, decision):

        if not self.ws:
            return

        try:
            izq, der = decision_to_motors(decision)

            cmd = {
                "K": izq * bias_i,
                "Q": der * bias_d,
                "D": 90,
                "M": 0,
                "E": 0,
                "F": 0,
                "duracion_ms": CMD_TIME
            }

            print(f"CMD -> {decision} | K:{cmd['K']} Q:{cmd['Q']}")

            await self.ws.send(json.dumps(cmd))

        except Exception as e:
            print("Error TX:", e)

    # ----------------------
    # LOOP RÁPIDO
    # ----------------------
    async def command_stream(self):
        while True:
            await self.send_command(self.current_command)
            await asyncio.sleep(self.send_interval)

    async def close(self):
        if self.ws:
            await self.ws.close()