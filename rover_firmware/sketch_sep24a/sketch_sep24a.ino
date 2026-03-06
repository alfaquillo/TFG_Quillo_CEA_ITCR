#include <Arduino_FreeRTOS.h>
#include <task.h>
#include <queue.h>
#include <supporting_functions.h>
#include <maes-rtos.h>
#include <SoftPWM.h>

using namespace MAES;
Agent_Platform AP_GALAXY_RVR("windows");

#include "mode_handler_agent.h"
#include "wifi_agent.h"
#include "peripherals_control_agent.h"
#include "sensor_control_agent.h"






void setup() {
  Serial.begin(115200);
  SoftPWMBegin();
  while (!Serial) {;}

  Serial.println(F("FreeMAES \n"));
  AP_GALAXY_RVR.agent_init(&WiFi_Agent, wifi);
  AP_GALAXY_RVR.agent_init(&Mode_Handler_Agent, mode);
  AP_GALAXY_RVR.agent_init(&Peripherals_Control, peripherals);
  AP_GALAXY_RVR.agent_init(&Sensor_Control, sensors);
	
  AP_GALAXY_RVR.boot();

  Serial.println(F("boot exitoso \n"));
  vTaskStartScheduler();
  for (;;);
}