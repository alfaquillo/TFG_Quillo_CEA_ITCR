/*
 * FreeMAES + FreeRTOS Demo: Sender / Receiver
 * --------------------------------------------
 * Versión adaptada para Arduino.
 * Incluye medición del idleCounter, deltaIdle y High-Water Mark de cada agente.
 * Autor: Oscar Fernández - SETEC / TEC
 */

#include <Arduino.h>
#include <Arduino_FreeRTOS.h>
#include <task.h>
#include <queue.h>
#include <supporting_functions.h>
#include <maes-rtos.h>

using namespace MAES;

/* ------------------- Declaración de agentes ------------------- */
Agent sender("Agent Sender", 1, 256);
Agent receiver("Agent Receiver", 2, 256);

/* ------------------- Variables de Idle Hook ------------------- */
extern volatile uint32_t idleCounter;  // definida en supporting_functions.cpp
static uint32_t lastIdle = 0;

/* ------------------- Prototipos ------------------- */
void write(void* pvParameters);
void read(void* pvParameters);

/* ------------------- Plataforma MAES ------------------- */
Agent_Platform AP("Arduino");

/* ------------------- Comportamiento del agente emisor ------------------- */
class writingBehaviour : public CyclicBehaviour {
public:
  void setup() override {
    msg.add_receiver(receiver.AID());
  }

  void action() override {
    Serial.println(F("Enviando mensaje..."));
    msg.set_msg_type(INFORM);
    msg.set_msg_content((char*)"Hola MAES!");
    msg.send();

    // Medición del watermark (stack libre mínimo)
    UBaseType_t wm = uxTaskGetStackHighWaterMark(NULL);
    Serial.print(F("[STACK] Sender high-water mark = "));
    Serial.print(wm);
    Serial.println(F(" words"));

    vTaskDelay(pdMS_TO_TICKS(1000));
  }
};

/* ------------------- Tarea asociada ------------------- */
void write(void* pvParameters) {
  writingBehaviour b;
  for (;;) b.execute();
}

/* ------------------- Comportamiento del agente receptor ------------------- */
class readingBehaviour : public CyclicBehaviour {
public:
  void action() override {
    Serial.println(F("Esperando mensaje..."));
    msg.receive(portMAX_DELAY);

    if (msg.get_msg_type() == INFORM) {
      Serial.print(F("Mensaje recibido: "));
      Serial.println(msg.get_msg_content());
    }

    // Medición del watermark (stack libre mínimo)
    UBaseType_t wm = uxTaskGetStackHighWaterMark(NULL);
    Serial.print(F("[STACK] Receiver high-water mark = "));
    Serial.print(wm);
    Serial.println(F(" words"));

    // Medición de Idle Hook
    uint32_t currentIdle = idleCounter;
    uint32_t deltaIdle = currentIdle - lastIdle;
    lastIdle = currentIdle;

    Serial.print(F("[IDLE DEBUG] idleCounter = "));
    Serial.print(currentIdle);
    Serial.print(F(" | deltaIdle = "));
    Serial.println(deltaIdle);
    Serial.println(F("--------------------------------"));
  }
};

/* ------------------- Tarea asociada ------------------- */
void read(void* pvParameters) {
  readingBehaviour b;
  for (;;) b.execute();
}

/* ------------------- Setup principal ------------------- */
void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println(F("FreeMAES Sender/Receiver Demo (Arduino)"));
  randomSeed(millis());

  // Inicialización de los agentes
  AP.agent_init(&sender, write);
  AP.agent_init(&receiver, read);

  AP.boot();
  Serial.println(F("Boot exitoso"));

  vTaskStartScheduler();
  for (;;);
}

/* ------------------- Loop vacío ------------------- */
void loop() {}