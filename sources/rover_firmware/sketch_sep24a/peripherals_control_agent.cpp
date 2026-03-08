#include "peripherals_control_agent.h"

/* ------------------- Instancia global ------------------- */
Agent Peripherals_Control("Peripherals Control Agent", 1, 192);

/* ------------------- Funciones de hardware ------------------- */

void carSetMotors(int8_t power0, int8_t power1) {
  bool dir[2];
  int8_t power[2] = { power0, power1 };
  int8_t newPower[2];

  for (uint8_t i = 0; i < 2; i++) {
    dir[i] = power[i] > 0;
    if (MOTOR_DIRECTIONS[i]) dir[i] = !dir[i];

    if (power[i] == 0) {
      SoftPWMSet(MOTOR_PINS[i*2], 0);
      SoftPWMSet(MOTOR_PINS[i*2+1], 0);
      continue;
    }

    newPower[i] = map(abs(power[i]), 0, 100, MOTOR_POWER_MIN, 255);
    SoftPWMSet(MOTOR_PINS[i*2], dir[i] * newPower[i]);
    SoftPWMSet(MOTOR_PINS[i*2+1], !dir[i] * newPower[i]);
  }
}

void setRGB(uint32_t color) {
  uint8_t r = (color >> 16) & 0xFF;
  uint8_t g = (color >> 8) & 0xFF;
  uint8_t b = (color) & 0xFF;

  r = int(r * R_OFFSET);
  g = int(g * G_OFFSET);
  b = int(b * B_OFFSET);

  for (uint8_t i = 0; i < 3; i++) pinMode(RGB_PINS[i], OUTPUT);
  analogWrite(RGB_PINS[0], r);
  analogWrite(RGB_PINS[1], g);
  analogWrite(RGB_PINS[2], b);
}

void setServo(uint8_t angle) {
  uint16_t pulseWidth = map(angle, 0, 180, 500, 2500);
  uint16_t value = map(pulseWidth, 0, 16666, 0, 255);
  SoftPWMSet(SERVO_PIN, value);
}

/* ------------------- Comportamiento del agente ------------------- */
class peripheralsBehaviour : public CyclicBehaviour {
public:
  void setup() override {
    for (uint8_t i = 0; i < 4; i++) pinMode(MOTOR_PINS[i], OUTPUT);
    for (uint8_t i = 0; i < 3; i++) pinMode(RGB_PINS[i], OUTPUT);
    pinMode(SERVO_PIN, OUTPUT);
    SoftPWMSet(SERVO_PIN, 0);
  }

  void action() override {
    peripheralsControlPackage* pkg;
    msg.receive(portMAX_DELAY);

    if (msg.get_msg_type() == INFORM) {
      pkg = (peripheralsControlPackage*) msg.get_msg_content();

      switch (pkg->type) {
        case PERIPH_MOTORS:
          switch (pkg->car.instruction) {
            case Car_Forward:  carSetMotors(pkg->car.power1, pkg->car.power1); break;
            case Car_Backward: carSetMotors(-pkg->car.power1, -pkg->car.power1); break;
            case Car_TurnLeft: carSetMotors(-pkg->car.power1, pkg->car.power1); break;
            case Car_TurnRight:carSetMotors(pkg->car.power1, -pkg->car.power1); break;
            case Car_SetMotors:carSetMotors(pkg->car.power1, pkg->car.power2); break;
            case Car_Stop:     carSetMotors(0, 0); break;
            default: break;
          }
          break;

        case PERIPH_RGB:
          if (pkg->rgb.instruction == RGB_Write)
            setRGB(pkg->rgb.color);
          else if (pkg->rgb.instruction == RGB_Off)
            setRGB(0x000000);
          break;

        case PERIPH_SERVO:
          if (pkg->servo.instruction == Servo_Write)
            setServo(pkg->servo.angle);
          break;

        default:
          break;
      }
    }
  }
};

/* ------------------- Tarea asociada ------------------- */
void peripherals(void* pvParameters) {
  peripheralsBehaviour b;
  b.execute();
}
