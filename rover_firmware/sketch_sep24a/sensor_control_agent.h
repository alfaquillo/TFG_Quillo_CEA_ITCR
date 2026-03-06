#ifndef SENSOR_CONTROL_AGENT_H
#define SENSOR_CONTROL_AGENT_H

#include <Arduino.h>
#include <Arduino_FreeRTOS.h>
#include <task.h>
#include <queue.h>
#include <supporting_functions.h>
#include <maes-rtos.h>

using namespace MAES;

/* ------------------- Pines Infrarrojos ------------------- */
#define IR_LEFT_PIN   8
#define IR_RIGHT_PIN  7

/* ------------------- Pines Ultrasónico ------------------- */
#define ULTRASONIC_TRIG_PIN  10
#define ULTRASONIC_ECHO_PIN  10

#define ULTRASONIC_AVOIDANCE_THRESHOLD 20  
#define MAX_DISTANCE 300                   
#define ULTRASONIC_READ_TIMEOUT 18000      

/* ------------------- Variables globales ------------------- */
extern byte ir_result;

extern float ultrasonic_distance;
extern bool  ultrasonic_IsObstacle;
extern bool  ultrasonic_IsClear;

/* ------------------- Declaración del agente ------------------- */
extern Agent Sensor_Control;

/* ------------------- Prototipo de la tarea ------------------- */
void sensors(void* pvParameters);

#endif // SENSOR_CONTROL_AGENT_H
