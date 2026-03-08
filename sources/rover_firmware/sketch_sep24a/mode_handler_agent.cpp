#include "mode_handler_agent.h"
#include "peripherals_control_agent.h"
#include "sensor_control_agent.h"

/* Instancia global del agente */
Agent Mode_Handler_Agent("Mode Handler Agent", 1, 192);

/* Variables estáticas para control de movimiento */
int8_t last_clear = -1;     // 1: izquierda fue la última zona libre, -1: derecha
bool last_forward = false;  // recuerda si el último movimiento fue hacia adelante

/* ---------------------------------------------------------- */
/* Comportamiento del agente Mode_Handler_Agent               */
/* ---------------------------------------------------------- */
class modeHandlerBehaviour : public CyclicBehaviour {
private:
  peripheralsControlPackage periph_pkg;

  rgbInstructions rgb_inst = RGB_Off;
  uint32_t color = 0x00000000;

  carInstructions car_inst = Car_Stop;
  int8_t power1 = 0;
  int8_t power2 = 0;

  servoInstructions servo_inst = Servo_Write;
  uint8_t angle = 90;

  /* ---------------- Obstacle Following ---------------- */
  carInstructions obstacleFollowing() {
    bool leftIsClear = bool(ir_result & 0b00000010);
    bool rightIsClear = bool(ir_result & 0b00000001);
    float usDistance = ultrasonic_distance;

    const float FOLLOW_DISTANCE = 15.0;      // cm
    const int8_t OBSTACLE_FOLLOW_POWER = 50; // %
    const int8_t SLOW_POWER = 30;

    if (usDistance < 4 && usDistance > 0) {
      return Car_Stop;
    } 
    else if (usDistance < 10 && usDistance > 0) {
      power1 = SLOW_POWER;
      power2 = SLOW_POWER;
      return Car_Forward;
    } 
    else if (usDistance < FOLLOW_DISTANCE && usDistance > 0) {
      power1 = OBSTACLE_FOLLOW_POWER;
      power2 = OBSTACLE_FOLLOW_POWER;
      return Car_Forward;
    } 
    else {
      if (!leftIsClear) {
        power1 = OBSTACLE_FOLLOW_POWER;
        power2 = -OBSTACLE_FOLLOW_POWER;
        return Car_TurnLeft;
      } 
      else if (!rightIsClear) {
        power1 = -OBSTACLE_FOLLOW_POWER;
        power2 = OBSTACLE_FOLLOW_POWER;
        return Car_TurnRight;
      } 
      else {
        return Car_Stop;
      }
    }
  }

  /* ---------------- Obstacle Avoidance ---------------- */
  carInstructions obstacleAvoidance() {
    bool leftIsClear = bool(ir_result & 0b00000010);  // sensor IR izquierdo
    bool rightIsClear = bool(ir_result & 0b00000001); // sensor IR derecho
    bool middleIsClear = ultrasonic_IsClear;          // distancia media

    const int8_t OBSTACLE_AVOID_POWER = 50;           // potencia de giro

    if (middleIsClear && leftIsClear && rightIsClear) {  // 111
      last_forward = true;
      power1 = OBSTACLE_AVOID_POWER;
      power2 = OBSTACLE_AVOID_POWER;
      return Car_Forward;
    } 
    else {
      if ((leftIsClear && rightIsClear) || (!leftIsClear && !rightIsClear)) { // 101, 000, 010
        if (last_clear == 1) {
          power1 = OBSTACLE_AVOID_POWER;
          power2 = -OBSTACLE_AVOID_POWER;
          last_forward = false;
          return Car_TurnLeft;
        } else {
          power1 = -OBSTACLE_AVOID_POWER;
          power2 = OBSTACLE_AVOID_POWER;
          last_forward = false;
          return Car_TurnRight;
        }
      } 
      else if (leftIsClear) {  // 100, 110
        if (last_clear == 1 || last_forward == true) {
          power1 = OBSTACLE_AVOID_POWER;
          power2 = -OBSTACLE_AVOID_POWER;
          last_clear = 1;
          last_forward = false;
          return Car_TurnLeft;
        }
      } 
      else if (rightIsClear) { // 001, 011
        if (last_clear == -1 || last_forward == true) {
          power1 = -OBSTACLE_AVOID_POWER;
          power2 = OBSTACLE_AVOID_POWER;
          last_clear = -1;
          last_forward = false;
          return Car_TurnRight;
        }
      }
    }

    return Car_Stop;
  }

public:
  void setup() override {
    msg.add_receiver(Peripherals_Control.AID());
  }

  void action() override {
    switch (currentMode) {
      case MODE_NONE:
        rgb_inst = RGB_Write;
        color = WHITE;
        car_inst = Car_Stop;
        power1 = 0;
        power2 = 0; 
        angle = 90;
        break;

      case MODE_DISCONNECT:
        rgb_inst = RGB_Write;
        color = RED;
        car_inst = Car_Stop;
        power1 = 0;
        power2 = 0;
        angle = 90;
        break;

      case MODE_OBSTACLE_FOLLOWING:
        rgb_inst = RGB_Write;
        color = BLUE;
        car_inst = obstacleFollowing();
        angle = servoAngle;
        break;

      case MODE_OBSTACLE_AVOIDANCE:
        rgb_inst = RGB_Write;
        color = PURPLE;
        car_inst = obstacleAvoidance();  
        angle = servoAngle;
        break;

      case MODE_APP_CONTROL:
        rgb_inst = RGB_Write;
        color = CYAN;
        car_inst = Car_SetMotors;
        power1 = leftMotorPower;
        power2 = rightMotorPower;
        angle = servoAngle;
        break;

      case MODE_VOICE_CONTROL:
        rgb_inst = RGB_Write;
        color = CYAN;
        car_inst = Car_TurnRight;
        power1 = 50;
        power2 = 0;
        angle = 90;
        break;

      default:
        break;
    }

    /* ---- Enviar paquete RGB ---- */
    periph_pkg.type = PERIPH_RGB;
    periph_pkg.rgb.instruction = rgb_inst;
    periph_pkg.rgb.color = color;
    msg.set_msg_content((char*)&periph_pkg);
    msg.set_msg_type(INFORM);
    msg.send(Peripherals_Control.AID(), 1);

    /* ---- Enviar paquete motores ---- */
    periph_pkg.type = PERIPH_MOTORS;
    periph_pkg.car.instruction = car_inst;
    periph_pkg.car.power1 = power1;
    periph_pkg.car.power2 = power2;
    msg.set_msg_content((char*)&periph_pkg);
    msg.set_msg_type(INFORM);
    msg.send(Peripherals_Control.AID(), 1);

    /* ---- Enviar paquete servo ---- */
    periph_pkg.type = PERIPH_SERVO;
    periph_pkg.servo.instruction = servo_inst;
    periph_pkg.servo.angle = angle;
    msg.set_msg_content((char*)&periph_pkg);
    msg.set_msg_type(INFORM);
    msg.send(Peripherals_Control.AID(), 1);
  }
};

/* ---------------------------------------------------------- */
/* Tarea asociada al agente Mode_Handler_Agent                */
/* ---------------------------------------------------------- */
void mode(void* pvParameters) {
  modeHandlerBehaviour b;
  b.execute();
}
