#include "sensor_control_agent.h"

/* ------------------- Instancia global ------------------- */
Agent Sensor_Control("Sensor Control Agent", 1, 192);

/* ------------------- Variables globales ------------------- */
byte  ir_result               = 0b00000000;
float ultrasonic_distance     = -1.0;
bool  ultrasonic_IsObstacle   = false;
bool  ultrasonic_IsClear      = false;

/* ---------------------------------------------------------- */
/* Funciones internas                                         */
/* ---------------------------------------------------------- */
static float readUltrasonicCM() {
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);

  float duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH, ULTRASONIC_READ_TIMEOUT);
  float distance = duration * 0.017; // cm
  if (distance > MAX_DISTANCE || distance == 0)
    return -1;
  return distance;
}

/* ---------------------------------------------------------- */
/* Comportamiento del agente Sensor_Control                   */
/* ---------------------------------------------------------- */
class sensorBehaviour : public CyclicBehaviour {
public:
  void setup() override {
    pinMode(IR_LEFT_PIN, INPUT);
    pinMode(IR_RIGHT_PIN, INPUT);
  }

  void action() override {
    /* --- Lectura de sensores infrarrojos --- */
    byte left = digitalRead(IR_LEFT_PIN);
    byte right = digitalRead(IR_RIGHT_PIN);
    ir_result = (left << 1) | right;

    /* --- Lectura del sensor ultrasónico --- */
    float distance = readUltrasonicCM();
    ultrasonic_distance = distance;

    if (distance < 0) {
      ultrasonic_IsObstacle = false;
      ultrasonic_IsClear = false;
    } else {
      ultrasonic_IsObstacle = (distance < ULTRASONIC_AVOIDANCE_THRESHOLD);
      ultrasonic_IsClear = (distance >= ULTRASONIC_AVOIDANCE_THRESHOLD);
    }

    /* Pequeña pausa para evitar saturar la CPU */
    vTaskDelay(pdMS_TO_TICKS(50));
  }
};

/* ---------------------------------------------------------- */
/* Tarea asociada                                             */
/* ---------------------------------------------------------- */
void sensors(void* pvParameters) {
  sensorBehaviour b;
  b.execute();
}
