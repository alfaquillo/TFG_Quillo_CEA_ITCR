#include "wifi_agent.h"
#include "mode_handler_agent.h"
//#include "rgb_agent.h"
//#include "car_control_agent.h"
//#include "soft_servo_agent.h"
#include "peripherals_control_agent.h"
#include "sensor_control_agent.h"



/* ------------------- Instancia global del agente ------------------- */
Agent WiFi_Agent("WiFi Communication Agent", 1, 500);

/* ------------------- Objeto de cámara ------------------- */
AiCamera aiCam = AiCamera(NAME, TYPE);

/* ------------------- Variables globales compartidas ------------------- */
WiFiInstructions  currentMode     = MODE_NONE;
int8_t            leftMotorPower  = 0;
int8_t            rightMotorPower = 0;
uint8_t           servoAngle      = 90;
bool              cam_lamp_status = false;
//byte              ir_result       = 0b00000000;
//float             us_distance     = 0;

/* ------------------- Función onReceive ------------------- */
void onReceive() {
  // Info Agentes
  aiCam.sendDoc["A1"] = uxTaskGetStackHighWaterMark(WiFi_Agent.AID());
  aiCam.sendDoc["A2"] = uxTaskGetStackHighWaterMark(Mode_Handler_Agent.AID());
  aiCam.sendDoc["A3"] = uxTaskGetStackHighWaterMark(Peripherals_Control.AID());
  aiCam.sendDoc["A4"] = uxTaskGetStackHighWaterMark(Sensor_Control.AID());
  //aiCam.sendDoc["A5"] = uxTaskGetStackHighWaterMark(Servo_Control.AID());

  // Voltaje de batería (comentado en original)
  // aiCam.sendDoc["BV"] = batteryGetVoltage();

  // Sensores infrarrojos
  aiCam.sendDoc["N"] = int(!bool(ir_result & 0b00000010));
  aiCam.sendDoc["P"] = int(!bool(ir_result & 0b00000001));

  // Sensor ultrasónico
  float us_result = int(ultrasonic_distance * 100) / 100.0;
  aiCam.sendDoc["O"] = us_result;

  // Botón de parada
  if (aiCam.getButton(REGION_I)) {
    currentMode = MODE_NONE;
    return;
  }

  // Selección de modos
  if (aiCam.getSwitch(REGION_E)) {
    if (currentMode != MODE_OBSTACLE_AVOIDANCE)
      currentMode = MODE_OBSTACLE_AVOIDANCE;
  } 
  else if (aiCam.getSwitch(REGION_F)) {
    if (currentMode != MODE_OBSTACLE_FOLLOWING)
      currentMode = MODE_OBSTACLE_FOLLOWING;
  } 
  else {
    if (currentMode == MODE_OBSTACLE_FOLLOWING || currentMode == MODE_OBSTACLE_AVOIDANCE) {
      currentMode = MODE_NONE;
      return;
    }
  }

  // Lámpara de cámara
  if (aiCam.getSwitch(REGION_M) && !cam_lamp_status) {
    Serial.println("lamp on");
    aiCam.lamp_on(5);
    cam_lamp_status = true;
  } 
  else if (!aiCam.getSwitch(REGION_M) && cam_lamp_status) {
    Serial.println("lamp off");
    aiCam.lamp_off();
    cam_lamp_status = false;
  }

  // Servo motor
  int temp = aiCam.getSlider(REGION_D);
  if (servoAngle != temp) {
    if (currentMode == MODE_NONE || currentMode == MODE_DISCONNECT)
      currentMode = MODE_APP_CONTROL;

    temp = constrain(temp, 0, 140);
    servoAngle = temp;
  }

  // Motores
  int throttle_L = aiCam.getThrottle(REGION_K);
  int throttle_R = aiCam.getThrottle(REGION_Q);

  //Serial.print("throttle_L: "); Serial.print(throttle_L);
  //Serial.print("  throttle_R: "); Serial.println(throttle_R);

  if (throttle_L != 0 || throttle_R != 0 || throttle_L != leftMotorPower || throttle_R != rightMotorPower) {
    currentMode = MODE_APP_CONTROL;
    leftMotorPower = throttle_L;
    rightMotorPower = throttle_R;
  }
}

/* ------------------- Comportamiento del agente ------------------- */
class wifiBehaviour : public CyclicBehaviour {
public:
  void setup() override {

    aiCam.begin(SSID, PASSWORD, WIFI_MODE, PORT);
    aiCam.setOnReceived(onReceive);
  }

  void action() override {
    //Serial.print(F("WiFi Agent | Watermark: "));
    //Serial.println(uxTaskGetStackHighWaterMark(NULL));

    aiCam.loop(); 
    /* --------------------------------------------------------------- */
    if (aiCam.ws_connected == false) {
      currentMode = MODE_DISCONNECT;
    } else {
      if (currentMode == MODE_DISCONNECT) {
        currentMode = MODE_NONE;
      }
    }



  }
};

/* ------------------- Tarea asociada ------------------- */
void wifi(void* pvParameters) {
  wifiBehaviour b;
  b.execute();
}