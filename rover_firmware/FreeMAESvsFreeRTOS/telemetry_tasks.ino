/*
 * FreeRTOS Demo: Telemetry
 * --------------------------------------------
 * Versión adaptada para Arduino.
 * Autor: Oscar Fernández - SETEC / TEC
 */


#include <Arduino.h>
#include <Arduino_FreeRTOS.h>
#include <task.h>
#include <queue.h>
#include <supporting_functions.h>

/* ------------------- Variables globales ------------------- */
extern volatile uint32_t idleCounter;  
static uint32_t lastIdle = 0;
static TickType_t lastTick = 0;

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

typedef struct message {
  meas_type type;
  char response[40];
} message;

/* ------------------- Colas ------------------- */
QueueHandle_t queueRequest;
QueueHandle_t queueResponse;

/* ------------------- Prototipos ------------------- */
void loggerTask(void* pvParameters);
void generatorTask(void* pvParameters);
void printIdleUsage(const char* name);

void printIdleUsage(const char* name) {
  uint32_t currentIdle = idleCounter;
  TickType_t currentTick = xTaskGetTickCount();

  uint32_t deltaIdle = currentIdle - lastIdle;
  TickType_t deltaTicks = currentTick - lastTick;
  if (deltaTicks == 0) deltaTicks = 1;

  lastIdle = currentIdle;
  lastTick = currentTick;

  float idlePercent = 100.0f * ((float)deltaIdle / (float)deltaTicks);
  if (idlePercent > 100.0f) idlePercent = 100.0f;

  Serial.print(F("[IDLE DEBUG] "));
  Serial.print(name);
  Serial.print(F(" | idleCounter="));
  Serial.print(currentIdle);
  Serial.print(F(" | deltaIdle="));
  Serial.print(deltaIdle);
  Serial.print(F(" | ticks="));
  Serial.print(deltaTicks);
  Serial.print(F(" | Idle%="));
  Serial.print(idlePercent, 2);
  Serial.println(F("%"));
}

/* ------------------- Tareas de loggers ------------------- */
void loggerTask(void* pvParameters) {
  logger_info* info = (logger_info*)pvParameters;
  message req, res;

  for (;;) {
    req.type = info->type;
    xQueueSend(queueRequest, &req, portMAX_DELAY);
    xQueueReceive(queueResponse, &res, portMAX_DELAY);

    switch (info->type) {
      case CURRENT: Serial.print(F("[Current Logger] ")); break;
      case VOLTAGE: Serial.print(F("[Voltage Logger] ")); break;
      case TEMPERATURE: Serial.print(F("[Temperature Logger] ")); break;
    }
    Serial.println(res.response);

    UBaseType_t wm = uxTaskGetStackHighWaterMark(NULL);
    Serial.print(F("[STACK] Logger high-water mark = "));
    Serial.print(wm);
    Serial.println(F(" words"));

    printIdleUsage("Logger");
    Serial.println(F("--------------------------------"));

    vTaskDelay(pdMS_TO_TICKS(info->rate));
  }
}

/* ------------------- Tarea del generador ------------------- */
void generatorTask(void* pvParameters) {
  (void) pvParameters;
  message req, res;

  for (;;) {
    xQueueReceive(queueRequest, &req, portMAX_DELAY);

    float value = 0.0;
    memset(res.response, 0, sizeof(res.response));  

    switch (req.type) {
      case CURRENT:
        value = 0.1 + (float)random(0, 1000) / 1000.0 * (1000.0 - 0.1);
        Serial.print(F("Current measurement: "));
        Serial.print(value, 2);
        Serial.println(F(" mA"));
        snprintf(res.response, sizeof(res.response) - 1, "%.2f mA", value);
        break;

      case VOLTAGE:
        value = 0.5 + (float)random(0, 1000) / 1000.0 * (3.3 - 0.5);
        Serial.print(F("Voltage measurement: "));
        Serial.print(value, 2);
        Serial.println(F(" V"));
        snprintf(res.response, sizeof(res.response) - 1, "%.2f V", value);
        break;

      case TEMPERATURE:
        value = 30.0 + (float)random(0, 1000) / 1000.0 * (100.0 - 30.0);
        Serial.print(F("Temperature measurement: "));
        Serial.print(value, 2);
        Serial.println(F(" C"));
        snprintf(res.response, sizeof(res.response) - 1, "%.2f C", value);
        break;
    }

    res.type = req.type;
    xQueueSend(queueResponse, &res, portMAX_DELAY);

    UBaseType_t wm = uxTaskGetStackHighWaterMark(NULL);
    Serial.print(F("[STACK] Generator high-water mark = "));
    Serial.print(wm);
    Serial.println(F(" words"));
  }
}

/* ------------------- Setup principal ------------------- */
void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println(F("FreeRTOS Telemetry Demo (No FreeMAES, Fixed Version)"));
  randomSeed(millis());

  queueRequest = xQueueCreate(5, sizeof(message));
  queueResponse = xQueueCreate(5, sizeof(message));

  if (queueRequest == NULL || queueResponse == NULL) {
    Serial.println(F("Error creando colas!"));
    while (1);
  }

  static logger_info log_current = {CURRENT, 500};
  static logger_info log_voltage = {VOLTAGE, 1000};
  static logger_info log_temperature = {TEMPERATURE, 2000};

  xTaskCreate(loggerTask, "Current", 256, &log_current, 3, NULL);
  xTaskCreate(loggerTask, "Voltage", 256, &log_voltage, 2, NULL);
  xTaskCreate(loggerTask, "Temp", 256, &log_temperature, 1, NULL);
  xTaskCreate(generatorTask, "Generator", 256, NULL, 3, NULL);

  Serial.println(F("Boot exitoso\n"));
  vTaskStartScheduler();
}

void loop() {}