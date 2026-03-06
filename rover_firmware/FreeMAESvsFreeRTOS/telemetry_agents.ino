/*
 * FreeMAES + FreeRTOS Demo: Telemetry (Arduino)
 * ---------------------------------------------
 * Adaptado por Oscar Fernández - SETEC / TEC
 * 
 * Características:
 *  - 3 agentes logger: corriente, voltaje, temperatura
 *  - 1 agente generador de mediciones
 *  - Cálculo de IdleCounter, deltaIdle y porcentaje Idle (%)
 *  - Medición del Stack High-Water Mark por agente
 */

#include <Arduino.h>
#include <Arduino_FreeRTOS.h>
#include <task.h>
#include <queue.h>
#include <supporting_functions.h>
#include <maes-rtos.h>

using namespace MAES;
#define AGENT_STACK_DEPTH 256  // ajustable según plataforma

/* ------------------- Variables globales para métricas ------------------- */
extern volatile uint32_t idleCounter;   // definida en supporting_functions.cpp
static uint32_t lastIdle = 0;
static TickType_t lastTick = 0;

/* ------------------- Agentes ------------------- */
Agent logger_current("Current Agent", 3, AGENT_STACK_DEPTH);
Agent logger_voltage("Voltage Agent", 2, AGENT_STACK_DEPTH);
Agent logger_temperature("Temperature Agent", 1, AGENT_STACK_DEPTH);
Agent measurement("Gen Agent", 3, AGENT_STACK_DEPTH);

/* ------------------- Plataforma ------------------- */
Agent_Platform AP_TELEMETRY("Arduino");

/* ------------------- Tipos y estructuras ------------------- */
typedef enum meas_type {
  CURRENT,
  VOLTAGE,
  TEMPERATURE
} meas_type;

typedef struct logger_info {
  meas_type type;
  UBaseType_t rate;
} logger_info;

logger_info log_current, log_voltage, log_temperature;

/* ------------------- Función auxiliar para medir Idle% ------------------- */
void printIdleUsage() {
  uint32_t currentIdle = idleCounter;
  TickType_t currentTick = xTaskGetTickCount();

  uint32_t deltaIdle = currentIdle - lastIdle;
  TickType_t deltaTicks = currentTick - lastTick;

  if (deltaTicks == 0) deltaTicks = 1;

  lastIdle = currentIdle;
  lastTick = currentTick;

  float idlePercent = 100.0f * ((float)deltaIdle / (float)deltaTicks);
  if (idlePercent > 100.0f) idlePercent = 100.0f;

  Serial.print(F("[IDLE DEBUG] idleCounter="));
  Serial.print(currentIdle);
  Serial.print(F(" | deltaIdle="));
  Serial.print(deltaIdle);
  Serial.print(F(" | ticks="));
  Serial.print(deltaTicks);
  Serial.print(F(" | Idle%="));
  Serial.print(idlePercent, 2);
  Serial.println(F("%"));
}

/* ------------------- Comportamiento de Loggers ------------------- */
class loggerBehaviour : public CyclicBehaviour {
public:
  logger_info* info;
  void setup() override {
    info = (logger_info*)taskParameters;
  }

  void action() override {
    msg.set_msg_content((char*)info->type);
    msg.send(measurement.AID(), portMAX_DELAY);
    msg.receive(portMAX_DELAY);

    // Mostrar medición recibida
    switch (info->type) {
      case CURRENT: Serial.print(F("[Current Logger] ")); break;
      case VOLTAGE: Serial.print(F("[Voltage Logger] ")); break;
      case TEMPERATURE: Serial.print(F("[Temperature Logger] ")); break;
    }
    Serial.println(msg.get_msg_content());

    // Mostrar Stack High-Water Mark
    UBaseType_t wm = uxTaskGetStackHighWaterMark(NULL);
    Serial.print(F("[STACK] "));
    Serial.print(AP_TELEMETRY.get_Agent_description(AP_TELEMETRY.get_running_agent()).agent_name);
    Serial.print(F(" high-water mark = "));
    Serial.print(wm);
    Serial.println(F(" words"));

    // Mostrar métricas Idle
    printIdleUsage();
    Serial.println(F("--------------------------------"));

    vTaskDelay(pdMS_TO_TICKS(info->rate));
  }
};

void logger(void* taskParameter) {
  loggerBehaviour b;
  b.taskParameters = taskParameter;
  for (;;) b.execute();
}

/* ------------------- Comportamiento del Generador ------------------- */
class genBehaviour : public CyclicBehaviour {
public:
  float min, max, value;

  void action() override {
    msg.receive(portMAX_DELAY);
    int type = (int)msg.get_msg_content();

    switch (type) {
      case CURRENT:
        min = 0.1;
        max = 1000.0;
        value = min + (float)random(0, 1000) / 1000.0 * (max - min);
        Serial.print(F("Current measurement: "));
        Serial.print(value, 2);
        Serial.println(F(" mA"));
        break;

      case VOLTAGE:
        min = 0.5;
        max = 3.3;
        value = min + (float)random(0, 1000) / 1000.0 * (max - min);
        Serial.print(F("Voltage measurement: "));
        Serial.print(value, 2);
        Serial.println(F(" V"));
        break;

      case TEMPERATURE:
        min = 30.0;
        max = 100.0;
        value = min + (float)random(0, 1000) / 1000.0 * (max - min);
        Serial.print(F("Temperature measurement: "));
        Serial.print(value, 2);
        Serial.println(F(" °C"));
        break;

      default:
        Serial.println(F("Unknown request"));
        break;
    }

    msg.set_msg_content((char*)"OK");
    msg.send(msg.get_sender(), portMAX_DELAY);

    // Medir Stack High-Water Mark
    UBaseType_t wm = uxTaskGetStackHighWaterMark(NULL);
    Serial.print(F("[STACK] Generator high-water mark = "));
    Serial.print(wm);
    Serial.println(F(" words"));
  }
};

void gen_meas(void* taskParameter) {
  genBehaviour b;
  for (;;) b.execute();
}

/* ------------------- Setup principal ------------------- */
void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println(F("FreeMAES Telemetry Demo (Idle % + Stack)"));
  randomSeed(millis());

  // Inicializar configuración de loggers
  log_current.rate = 500;
  log_voltage.rate = 1000;
  log_temperature.rate = 2000;
  log_current.type = CURRENT;
  log_voltage.type = VOLTAGE;
  log_temperature.type = TEMPERATURE;

  // Inicialización de agentes
  AP_TELEMETRY.agent_init(&logger_current, logger, (void*)&log_current);
  AP_TELEMETRY.agent_init(&logger_voltage, logger, (void*)&log_voltage);
  AP_TELEMETRY.agent_init(&logger_temperature, logger, (void*)&log_temperature);
  AP_TELEMETRY.agent_init(&measurement, gen_meas);

  AP_TELEMETRY.boot();
  Serial.println(F("Boot exitoso\n"));
  vTaskStartScheduler();

  for (;;);
}

/* ------------------- Loop vacío ------------------- */
void loop() {}