#ifndef WIFI_AGENT_H
#define WIFI_AGENT_H

#include <Arduino.h>
#include <Arduino_FreeRTOS.h>
#include <task.h>
#include <queue.h>
#include <supporting_functions.h>
#include <maes-rtos.h>
#include <SoftPWM.h>
#include <SunFounder_AI_Camera.h>

using namespace MAES;

/* ------------------- Configuración WiFi STA------------------- */
#define WIFI_MODE WIFI_MODE_STA
#define SSID      "Moon_rpi_AP"
#define PASSWORD  "seteclab2026"
#define NAME      "GalaxyRVR"
#define TYPE      "GalaxyRVR"
#define PORT      "8765"
#define WS_HEADER "WS+"



/* ------------------- Configuración WiFi AP ------------------- */
//#define WIFI_MODE WIFI_MODE_AP
//#define SSID      "GalaxyRVR_MAS"
//#define PASSWORD  "111222333"
//#define NAME      "GalaxyRVR"
//#define TYPE      "GalaxyRVR"
//#define PORT      "8765"
//#define WS_HEADER "WS+"


/* ------------------- Modos de operación ------------------- */
// #define MODE_NONE                    0
// #define MODE_OBSTACLE_FOLLOWING      1
// #define MODE_OBSTACLE_AVOIDANCE      2
// #define MODE_APP_CONTROL             3
// #define MODE_VOICE_CONTROL           4
// #define MODE_DISCONNECT              5


typedef enum WiFiInstructions : uint8_t {
  MODE_NONE,
  MODE_OBSTACLE_FOLLOWING,
  MODE_OBSTACLE_AVOIDANCE,
  MODE_APP_CONTROL,
  MODE_VOICE_CONTROL,
  MODE_DISCONNECT
} WIFIInstructions;


typedef struct {
    WiFiInstructions instruction;
} WiFiPackage;

/* ------------------- Variables globales ------------------- */
extern WiFiInstructions currentMode;
extern int8_t leftMotorPower;
extern int8_t rightMotorPower;
extern uint8_t servoAngle;
extern bool cam_lamp_status;
extern byte ir_result;
extern float us_distance;

/* ------------------- Declaraciones de objetos ------------------- */
extern AiCamera aiCam;

/* ------------------- Declaración del agente ------------------- */
extern Agent WiFi_Agent;

/* ------------------- Prototipo de función de tarea ------------------- */
void wifi(void* pvParameters);

#endif // WIFI_AGENT_H