import asyncio
import json
import websockets

URI = "ws://192.168.4.1:8765"


async def test():
    while True:
        try:
            async with websockets.connect(URI) as ws:
                print("Conectado al websocket\n")

                async def sender():
                    while True:
                        try:
                            
                            await ws.send(json.dumps({"ping": 1}))
                            await asyncio.sleep(0.3)  # 300 ms
                        except:
                            break

                async def receiver():
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

                        # SOLO MENSAJES DE SENSORES
                        if "O" not in data:
                            continue

                        prox_izq = data.get("N", 0)
                        prox_der = data.get("P", 0)
                        dist = data.get("O", -1)

                        print("-----")
                        print(f"IR  -> izq: {prox_izq} | der: {prox_der}")

                        if dist < 0:
                            print("LIDAR -> inválido")
                        else:
                            print(f"LIDAR -> {dist:.2f} cm")

                await asyncio.gather(sender(), receiver())

        except Exception as e:
            print("Error conexión:", e)
            print("Reintentando...\n")
            await asyncio.sleep(1)

asyncio.run(test())