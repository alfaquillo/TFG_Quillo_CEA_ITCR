import asyncio
import json
import websockets
from config import WS_URI, PING_INTERVAL, DEFAULT_IR, DEFAULT_LIDAR


class Sensors:
    def __init__(self):
        self.prox_izq = DEFAULT_IR
        self.prox_der = DEFAULT_IR
        self.dist = DEFAULT_LIDAR
        self.connected = False

    async def connect(self):
        while True:
            try:
                async with websockets.connect(WS_URI) as ws:
                    self.connected = True
                    print("Sensores conectados\n")

                    await asyncio.gather(
                        self._sender(ws),
                        self._receiver(ws)
                    )

            except Exception as e:
                self.connected = False
                print("Error sensores:", e)
                await asyncio.sleep(1)

    async def _sender(self, ws):
        while True:
            try:
                await ws.send(json.dumps({"ping": 1}))
                await asyncio.sleep(PING_INTERVAL)
            except:
                break

    async def _receiver(self, ws):
        async for message in ws:

            if isinstance(message, bytes):
                continue

            if not message or not message.strip():
                continue

            try:
                data = json.loads(message)
            except:
                continue

            if not isinstance(data, dict):
                continue

            if "O" not in data:
                continue
            
            self.prox_izq = data.get("N", DEFAULT_IR)
            self.prox_der = data.get("P", DEFAULT_IR)
            self.dist = data.get("O", DEFAULT_LIDAR)

    def get_data(self):
        return {
            "izq": self.prox_izq,
            "der": self.prox_der,
            "dist": self.dist,
            "connected": self.connected
        }