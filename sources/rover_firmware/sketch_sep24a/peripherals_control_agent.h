#ifndef PERIPHERALS_CONTROL_AGENT_H
#define PERIPHERALS_CONTROL_AGENT_H

#include <Arduino.h>
#include <Arduino_FreeRTOS.h>
#include <task.h>
#include <queue.h>
#include <SoftPWM.h>
#include <supporting_functions.h>
#include <maes-rtos.h>

using namespace MAES;

/* ===================== DEFINICIÓN DE HARDWARE ===================== */

/* ---- Motores ---- */
#define MOTOR_PINS       (uint8_t[4]){2, 3, 4, 5}
#define MOTOR_DIRECTIONS (uint8_t[2]){0, 1}
#define MOTOR_POWER_MIN  28

/* ---- Servo ---- */
#define SERVO_PIN 6

/* ---- RGB ---- */
#define COMMON_ANODE 0
#define RGB_PINS (uint8_t[3]){12, 13, 11}

/* Colores predefinidos */
#define RED           0xFF0202
#define BLUE          0x0A0AFF
#define GREEN         0x0AFF0A
#define CYAN          0x0AFFFF
#define PURPLE        0xA50AFF
#define YELLOW        0xFFFF0A
#define WHITE         0xFFFFFF

/* Calibración brillo */
#define R_OFFSET 1.0
#define G_OFFSET 0.25
#define B_OFFSET 0.45

/* ===================== ENUMERACIONES ===================== */

/* Tipos de periféricos controlables */
typedef enum peripheralsType : uint8_t {
  PERIPH_MOTORS,
  PERIPH_RGB,
  PERIPH_SERVO
} peripheralsType;

/* Instrucciones para cada subsistema */
typedef enum carInstructions : uint8_t {
  Car_Begin,
  Car_Forward,
  Car_Backward,
  Car_TurnLeft,
  Car_TurnRight,
  Car_Stop,
  Car_SetMotors
} carInstructions;

typedef enum rgbInstructions : uint8_t {
  RGB_Begin,
  RGB_Write,
  RGB_Off
} rgbInstructions;

typedef enum servoInstructions : uint8_t {
  Servo_Write
} servoInstructions;

/* ===================== ESTRUCTURAS DE PAQUETES ===================== */

typedef struct {
  carInstructions instruction;
  int8_t power1;
  int8_t power2;
} carControlPackage;

typedef struct {
  rgbInstructions instruction;
  uint32_t color;
} rgbControlPackage;

typedef struct {
  servoInstructions instruction;
  uint8_t angle;
} servoControlPackage;

/* Paquete unificado */
typedef struct {
  peripheralsType type;
  union {
    carControlPackage car;
    rgbControlPackage rgb;
    servoControlPackage servo;
  };
} peripheralsControlPackage;

/* ===================== DECLARACIONES ===================== */
extern Agent Peripherals_Control;

/* Tarea asociada */
void peripherals(void* pvParameters);

/* Funciones internas */
void carSetMotors(int8_t power0, int8_t power1);
void setRGB(uint32_t color);
void setServo(uint8_t angle);

#endif // PERIPHERALS_CONTROL_AGENT_H
