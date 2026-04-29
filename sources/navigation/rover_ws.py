import asyncio
import websockets
import json
import time
import re

from config import WS_URI
from sensors import Sensors
from navigation import decide_direction

VEL_MAX = 6
CMD_TIME = 400
bias_d = 1.3
bias_i = 1
OVERRIDE_CYCLES = 3


def decision_to_motors(decision):

    if decision.startswith("sens_"):
        decision = decision.replace("sens_", "")
    elif decision.startswith("nav_"):
        decision = decision.replace("nav_", "")

    if decision == "ADELANTE":
        return 1.0, 1.0
    elif decision == "IZQUIERDA":
        return 0.6, 1
    elif decision == "DERECHA":
        return 1, 0.6
    elif decision == "RETROCEDER":
        return -1.0, -1.0

    return 0.0, 0.0


class RoverClient:

    def __init__(self, uri=WS_URI):
        self.uri = uri
        self.ws = None

        self.sensors = Sensors()

        self.last_override = "LIBRE"
        self.override_timer = 0

        self.current_command = "nav_ADELANTE"
        self.send_interval = 0.1

        self.connected = False
        self.reconnecting = False

        self.last_rx_time = time.time()


    # ----------------------
    # CONEXIÓN
    # ----------------------
    async def connect(self):

        if self.connected:
            return

        try:
            self.ws = await websockets.connect(
                self.uri,
                ping_interval=None,
                ping_timeout=None
            )

            self.connected = True
            self.last_rx_time = time.time()

            print("[WS] Conectado al rover")

            await self.ws.send(json.dumps({"D": 90}))

            if not hasattr(self, "rx_task") or self.rx_task.done():
                self.rx_task = asyncio.create_task(self.receiver_loop())

            if not hasattr(self, "tx_task") or self.tx_task.done():
                self.tx_task = asyncio.create_task(self.command_stream())

        except Exception as e:
            print("[WS] Error conexión:", e)
            await asyncio.sleep(1)
            await self.reconnect()


    async def reconnect(self):
        if self.reconnecting:
            return

        self.reconnecting = True
        self.connected = False

        try:
            if self.ws:
                await self.ws.close()
        except:
            pass

        print("[WS] Reconectando...")

        while not self.connected:
            try:
                await asyncio.sleep(1)

                self.ws = await websockets.connect(
                    self.uri,
                    ping_interval=None,
                    ping_timeout=None
                )

                self.connected = True
                self.last_rx_time = time.time()

                print("[WS] Reconectado")


            except Exception as e:
                print("[WS] Reintento falló:", e)

        self.reconnecting = False


    # ----------------------
    # RECEPCIÓN
    # ----------------------
    async def receiver_loop(self):
        while True:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=3)

                if not message:
                    continue

                self.last_rx_time = time.time()

                if isinstance(message, bytes):
                    continue

                if isinstance(message, str):
                    print("Message_data_test", message)

                    # -------- LIMPIEZA BASE --------
                    # quitar prefijo WS+
                    if "WS+" in message:
                        message = message.split("WS+")[-1]

                    message = message.strip()

                    
                    if "{" not in message:
                        continue

                    
                    start = message.find("{")
                    end = message.rfind("}") + 1

                    if start == -1 or end == 0:
                        continue

                    message = message[start:end]

                # -------- PARSEO --------
                try:
                    data = json.loads(message)
                except:
                    continue

                # -------- PING → PONG --------
                if "ping" in data:
                    await self.ws.send(json.dumps({
                        "pong": data["ping"]
                    }))
                    continue

                # -------- UPDATE SENSORES --------
                self.sensors.update(data)

            except asyncio.TimeoutError:
                continue

            except Exception as e:
                print("[WS] Error RX:", e)

                if self.connected and not self.reconnecting:
                    self.connected = False
                    await self.reconnect()

                continue

    # ----------------------
    # DECISIÓN
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

        if not self.connected:
            return

        try:
            MAX_MOTOR = 20

            scale_izq, scale_der = decision_to_motors(decision)

            izq = VEL_MAX * scale_izq * bias_i
            der = VEL_MAX * scale_der * bias_d

            max_val = max(abs(izq), abs(der))

            if max_val > MAX_MOTOR:
                factor = MAX_MOTOR / max_val
                izq *= factor
                der *= factor

            cmd = {
                "K": int(round(izq)),
                "Q": int(round(der)),
                "M": 1,
                "duracion_ms": int(CMD_TIME)
            }

            print(f"CMD -> {decision} | K:{cmd['K']} Q:{cmd['Q']}")

            await self.ws.send(json.dumps(cmd))

        except Exception as e:
            print("[WS] Error TX:", e)

            if self.connected and not self.reconnecting:
                self.connected = False
                await self.reconnect()


    # ----------------------
    # LOOP DE ENVÍO
    # ----------------------
    async def command_stream(self):
        while True:
            try:
                if self.connected:


                    if time.time() - self.last_rx_time > 5:
                        print("[WS] Sin datos RX por 5s → reconectando")

                        if not self.reconnecting:
                            self.connected = False
                            await self.reconnect()

                        continue

                    await self.send_command(self.current_command)

                await asyncio.sleep(self.send_interval)

            except Exception as e:
                print("[WS] Error loop TX:", e)
                self.connected = False
                await asyncio.sleep(0.5)


    # ----------------------
    # CIERRE
    # ----------------------
    async def close(self):
        self.connected = False
        if self.ws:
            await self.ws.close()