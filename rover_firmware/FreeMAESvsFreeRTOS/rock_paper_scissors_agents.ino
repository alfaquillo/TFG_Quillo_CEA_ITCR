/*
 * FreeMAES + FreeRTOS Demo: Rock Paper Scissors
 * --------------------------------------------
 * Autor: Oscar Fernández - SETEC / TEC
 */

#include <Arduino.h>
#include <Arduino_FreeRTOS.h>
#include <task.h>
#include <queue.h>
#include <supporting_functions.h>
#include <maes-rtos.h>

using namespace MAES;

/* ------------------- Agentes ------------------- */
Agent PlayerA("Player A", 1, 256);
Agent PlayerB("Player B", 1, 256);
Agent Referee("Referee", 2, 256);

/* ------------------- Declaración de tareas ------------------- */
void play(void* pvParameters);
void watchover(void* pvParameters);

/* ------------------- Plataforma MAES ------------------- */
Agent_Platform AP_RPS("Arduino");

/* ------------------- Variables Idle Hook ------------------- */
extern volatile uint32_t idleCounter; 
static uint32_t lastIdle = 0;

/* ------------------- Funciones auxiliares ------------------- */
int getRandom() {
  return random(0, 3);  
}

int choices(const char* msg) {
  if (strcmp(msg, "ROCK") == 0) return 0;
  else if (strcmp(msg, "PAPER") == 0) return 1;
  else return 2; 
}

/* ------------------- Comportamiento de Jugadores ------------------- */
class playingBehaviour : public CyclicBehaviour {
public:
  void setup() override {
    msg.add_receiver(Referee.AID());
  }

  void action() override {
    Serial.print(AP_RPS.get_Agent_description(AP_RPS.get_running_agent()).agent_name);
    Serial.println(F(": Rock, Paper, Scissors..."));

    vTaskDelay(pdMS_TO_TICKS(100));

    int num = getRandom();
    const char* bet;

    switch (num) {
      case 0: bet = "ROCK"; break;
      case 1: bet = "PAPER"; break;
      default: bet = "SCISSORS"; break;
    }

    msg.set_msg_content((char*)bet);
    msg.set_msg_type(INFORM);
    msg.send();

    /* ---- Imprimir watermark del agente ---- */
    TaskHandle_t hTask = xTaskGetCurrentTaskHandle();
    UBaseType_t watermark = uxTaskGetStackHighWaterMark(hTask);
    //Serial.print(F("[STACK] "));
    //Serial.print(AP_RPS.get_Agent_description(AP_RPS.get_running_agent()).agent_name);
    //Serial.print(F(" high-water mark = "));
    //Serial.print(watermark);
    //Serial.println(F(" words"));
  }
};

/* ------------------- Tarea asociada ------------------- */
void play(void* pvParameters) {
  playingBehaviour b;
  for (;;) {      
    b.execute();
  }
}

/* ------------------- Comportamiento del Árbitro ------------------- */
class watchoverBehaviour : public OneShotBehaviour {
public:
  void setup() override {
    msg.add_receiver(PlayerA.AID());
    msg.add_receiver(PlayerB.AID());
  }

  void action() override {
    char* msgA = nullptr;
    char* msgB = nullptr;
    int choiceA = -1;
    int choiceB = -1;

    int winner[3][3] = {
      {0, 2, 1},
      {1, 0, 2},
      {2, 1, 0}
    };

    Serial.println(F("\nREFEREE READY"));

    while (true) {
      msg.receive(portMAX_DELAY);

      if (msg.get_msg_type() == INFORM) {
        Serial.print(F("Playing now: "));
        Serial.print(AP_RPS.get_Agent_description(msg.get_sender()).agent_name);
        Serial.print(F(" -> "));
        Serial.println(msg.get_msg_content());

        if (msg.get_sender() == PlayerA.AID()) {
          msgA = msg.get_msg_content();
          choiceA = choices(msgA);
        } else if (msg.get_sender() == PlayerB.AID()) {
          msgB = msg.get_msg_content();
          choiceB = choices(msgB);
        }

        msg.suspend(msg.get_sender());
      }

      if (AP_RPS.get_state(PlayerA.AID()) == SUSPENDED &&
          AP_RPS.get_state(PlayerB.AID()) == SUSPENDED) {
        break;
      }
    }

    switch (winner[choiceA][choiceB]) {
      case 0: Serial.println(F("DRAW!")); break;
      case 1: Serial.println(F("PLAYER A WINS!")); break;
      case 2: Serial.println(F("PLAYER B WINS!")); break;
    }

    vTaskDelay(pdMS_TO_TICKS(2000));

    msg.resume(PlayerA.AID());
    msg.resume(PlayerB.AID());

    // ---- Mostrar idleCounter y deltaIdle ----
    uint32_t currentIdle = idleCounter;
    uint32_t deltaIdle = currentIdle - lastIdle;
    lastIdle = currentIdle;

    //Serial.print(F("\n[IDLE DEBUG] idleCounter = "));
    //Serial.print(currentIdle);
    //Serial.print(F(" | deltaIdle = "));
    //Serial.println(deltaIdle);

    // ---- Imprimir watermark del árbitro ----
    TaskHandle_t hTask = xTaskGetCurrentTaskHandle();
    UBaseType_t watermark = uxTaskGetStackHighWaterMark(hTask);
    //Serial.print(F("[STACK] Referee high-water mark = "));
    //Serial.print(watermark);
    //Serial.println(F(" words"));

    //Serial.println(F("-------------------------------------------"));
  }
};

/* ------------------- Tarea asociada ------------------- */
void watchover(void* pvParameters) {
  watchoverBehaviour b;  
  for (;;) {             
    b.execute();
  }
}

/* ------------------- Setup principal ------------------- */
void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println(F("FreeMAES RPS Demo"));

  // Inicialización de agentes
  AP_RPS.agent_init(&PlayerA, play);
  Serial.println(F("Player A Agent Inicializado"));
  AP_RPS.agent_init(&PlayerB, play);
  Serial.println(F("Player B Agent Inicializado"));
  AP_RPS.agent_init(&Referee, watchover);
  Serial.println(F("Referee Agent Inicializado"));

  AP_RPS.boot();
  Serial.println(F("Boot exitoso"));

  vTaskStartScheduler();
  for (;;);
}

/* ------------------- Loop vacío ------------------- */
void loop() {}
