#ifndef MODE_HANDLER_AGENT_H
#define MODE_HANDLER_AGENT_H

#include <Arduino.h>
#include <Arduino_FreeRTOS.h>
#include <task.h>
#include <queue.h>
#include <supporting_functions.h>
#include <maes-rtos.h>

#include "wifi_agent.h"  // para acceder a WiFiPackage y WiFiInstructions

using namespace MAES;

/* Declaración global del agente */
extern Agent Mode_Handler_Agent;

/* variables of rgb_blink when disconnected */
extern uint32_t rgb_blink_interval; // uint: ms
extern uint32_t rgb_blink_start_time;
extern bool rgb_blink_flag;

/* Prototipo de la tarea asociada */
void mode(void* pvParameters);

#endif // MODE_HANDLER_AGENT_H