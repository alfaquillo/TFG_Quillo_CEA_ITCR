import time
from config import DEFAULT_IR, DEFAULT_LIDAR


class Sensors:
    def __init__(self):
        self.prox_izq = DEFAULT_IR
        self.prox_der = DEFAULT_IR
        self.dist = DEFAULT_LIDAR
        self.connected = False

        self.lidar_block_count = 0
        self.current_action = "LIBRE"
        self.action_until = 0

    # -----------------------------
    # ACTUALIZACIÓN DESDE WEBSOCKET
    # -----------------------------
    def update(self, data):

        if not isinstance(data, dict):
            return

        if "O" not in data:
            return

        self.prox_izq = data.get("N", DEFAULT_IR)
        self.prox_der = data.get("P", DEFAULT_IR)
        self.dist = data.get("O", DEFAULT_LIDAR)

        self.connected = True

    # -----------------------------
    # LÓGICA DE EVASIÓN
    # -----------------------------
    def decide_avoidance(self, th_dist=30):

        now = time.time()

        print(f"[SENS] IZQ={self.prox_izq} DER={self.prox_der} LIDAR={self.dist}")

        if not self.connected:
            return "LIBRE"

        # mantener acción
        if now < self.action_until:
            return self.current_action

        # ----------------------------------
        # LÓGICA LIDAR CON HYSTERESIS
        # ----------------------------------

        TH_ENTER = 30
        TH_EXIT = 45

        

        # si estamos retrocediendo → evaluar salida
        if self.current_action == "RETROCEDER":

            if self.dist == -1 or self.dist > TH_EXIT:
                self.current_action = "LIBRE"
                return "LIBRE"

            return "RETROCEDER"


        # si NO estamos retrocediendo → evaluar entrada
        if self.dist != -1 and self.dist < TH_ENTER:
            self.current_action = "RETROCEDER"
            self.action_until = now + 0.8
            return "RETROCEDER"
        
        # timeout de seguridad
        if self.current_action == "RETROCEDER" and now > self.action_until:
            self.current_action = "LIBRE"
            return "LIBRE"

        # IR
        if self.prox_izq == 1:
            self.current_action = "RETROCEDER"
            self.action_until = now + 0.5
            self.current_action = "DERECHA"
            self.action_until = now + 0.5
            return self.current_action

        if self.prox_der == 1:
            self.current_action = "RETROCEDER"
            self.action_until = now + 0.5
            self.current_action = "IZQUIERDA"
            self.action_until = now + 0.5
            return self.current_action

        return "LIBRE"