# FreeMAES for ATmega Devices 🚀  
*Adaptation of the FreeMAES library for embedded MAS development on ATmega microcontrollers.*

---

## 🛰 Overview

This project provides an **adaptation of the [FreeMAES](https://github.com/DRoMarin/FreeMAES.git)** multi-agent framework to **Microchip ATmega-based devices**, enabling distributed agent-based applications on low-resource embedded platforms.

Additionally, it includes a complete **Multi-Agent System (MAS)** implementation developed for the **SunFounder Galaxy RVR** rover.

---

## 🧩 Requirements

FreeMAES works in conjunction with the real-time operating system **FreeRTOS**, so it is required to install FreeRTOS before using this library.

You can install it through the **Arduino IDE Library Manager**:

1. Open **Arduino IDE** → go to **Sketch → Include Library → Manage Libraries…**
2. Search for **“FreeRTOS”** by *Richard Barry*
3. Install **version 11** (Note: newer versions *may* work, but are not guaranteed)

> ⚠️ **Important:**  
> This repository includes a custom `FreeRTOSConfig.h` file.  
> Make sure to use this version instead of the original one provided by the FreeRTOS library.

---

## ⚙️ How to Install the Library

It is recommended that you use **Arduino IDE** for implementing this library.

### Installation Steps

1. Add both **Supporting_Functions** and **maes-rtos** folders to your Arduino IDE `libraries` directory.  
2. Open Arduino IDE → **Sketch → Include Library** → under *Contributed Libraries*, add:  
   - `Supporting_Functions`  
   - `maes-rtos`  
3. Restart Arduino IDE.  
4. Include both libraries at the start of your project:

```cpp
#include <supporting_functions.h>
#include <maes-rtos.h>
```

---

## 🤖 GalaxyRVR MAS Project

This repository also includes a **Multi-Agent System (MAS)** implementation for the **SunFounder Galaxy RVR** rover.  
It was deployed on the Galaxy RVR using an **Arduino Mega 2560**, replacing the original **Arduino Uno R3** (for reasons explained in the *Recommendations* section).

The MAS consists of **four cooperative agents**, each responsible for a key subsystem of the rover:

| Agent | Description | Source Files |
|--------|--------------|--------------|
| **WiFi Agent** | Establishes and maintains the Wi-Fi connection with the **GalaxyRVR Control App**, and manages all incoming/outgoing communication packets. | `wifi_agent.cpp / .h` |
| **Mode Handler Agent** | Controls the logic associated with each operating mode (Manual, Systematic, and Monitor), and initializes the **autonomous control modes** for *object following* and *obstacle avoidance*. | `mode_handler_agent.cpp / .h` |
| **Sensor Control Agent** | Manages the **infrared sensors** and the **ultrasonic distance sensor**, providing perception data to the other agents. | `sensor_control_agent.cpp / .h` |
| **Peripherals Control Agent** | Handles the **servo motor**, **wheel motors**, and **RGB lights**, executing the commands received from the mode handler or the user application. | `peripherals_control_agent.cpp / .h` |

Each agent is implemented as a **FreeMAES agent task** running on **FreeRTOS**, ensuring modularity, parallelism, and robust inter-agent communication.

> 🧠 This MAS is designed to operate **in conjunction with the [GalaxyRVR Control App](https://github.com/Oscar-FZ/GalaxyRVR-Control-App.git)**, which provides a user interface for manual and autonomous rover control, telemetry visualization, and system monitoring.

---

## 🧪 FreeMAES vs FreeRTOS Comparison

Inside this repository, the folder **`FreeMAESvsFreeRTOS`** contains a set of six example programs used to compare the performance and memory footprint between **FreeRTOS task-based systems** and **FreeMAES agent-based systems**.

The folder includes three different projects, each with two versions:

| Project | FreeRTOS Version | FreeMAES + FreeRTOS Version | Description |
|----------|------------------|-----------------------------|--------------|
| **Rock Paper Scissors** | `rock_paper_scissors_tasks.ino` | `rock_paper_scissors_agents.ino` | Demonstrates multi-entity interaction logic using either tasks or agents. |
| **Sender Receiver** | `sender_receiver_tasks.ino` | `sender_receiver_agents.ino` | Compares message passing and synchronization efficiency between both systems. |
| **Telemetry** | `telemetry_tasks.ino` | `telemetry_agents.ino` | Simulates sensor data transmission and logging in both paradigms. |

These examples were used for analytical testing of **program size**, **stack usage**, and **CPU usage**, highlighting the advantages of the FreeMAES agent abstraction over standard FreeRTOS tasks in modular embedded architectures.

---

## 💡 Recommendations

It is **highly recommended** to use FreeMAES on devices with **higher SRAM capacity**.

Initially, the GalaxyRVR MAS was implemented on an **Arduino Uno R3 (2 kB SRAM)** — it worked, but the limited memory only allowed the use of two simple agents.

If you plan to implement a more complex MAS, consider using devices with larger SRAM:

| Device | Microcontroller | Flash | SRAM | EEPROM | Recommendation |
|---------|----------------|------|------|------|------|
| Arduino UNO Mini | ATmega328P | 32kB | 2kB | 1kB | - |
| Arduino UNO Rev3 | ATmega328P | 32kB | 2kB | 1kB | - |
| Arduino UNO WiFi Rev2 | ATmega4809 | 48kB | 6kB | 256B | ✅ |
| Arduino Leonardo | ATmega32u4 | 32kB | 2.5kB	 | 1kB | - |
| Arduino Mega 2560 Rev3 | ATmega2560 | 256kB | 8kB | 4kB | ✅ |
| Arduino Micro | ATmega32u4 | 32kB | 2.5kB | 1kB | - |

---

## 🧑‍💻 Author

**Óscar Fernández Zúñiga**  
Instituto Tecnológico de Costa Rica (TEC)  
School of Electronics Engineering  
**SETEC Lab – Space Systems Laboratory**
