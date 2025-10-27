# 🚗 Driver Drowsiness Detection System  

> ⚡ A Computer Vision + IoT project that keeps you awake on the road.  

This system uses **MediaPipe Face Mesh** and **OpenCV** to monitor the driver’s eyes in real time.  
When it detects that the driver is sleepy (eyes closed for too long), it:  
- Triggers a **buzzer** sound on the PC,  
- Turns the **LED from green to red**, and  
- **Stops the motor** (simulating the car halting).  

All of this happens through **WiFi communication** with an **ESP8266 NodeMCU**,  
making this a cool blend of **AI + IoT safety automation**.  

---

## ✨ Features
- ✅ Real-time eye closure detection using **MediaPipe FaceMesh**  
- ✅ Wireless communication between **Python app ↔ NodeMCU (ESP8266)**  
- ✅ Smart hardware response:
  - 🟢 **Green LED** → Driver awake  
  - 🔴 **Red LED** → Driver drowsy  
  - ⚙️ **Motor ON/OFF** → Simulated vehicle control  
  - 🔊 **PC-based buzzer** → Audible drowsiness alert  
- ✅ On-screen status overlay for:
  - Driver State: `ACTIVE / SLEEPING / NO FACE`
  - NodeMCU Connection: `Connected / Disconnected`

---

## 🧩 Hardware Requirements

| Component | Description |
|------------|-------------|
| **ESP8266 NodeMCU** | Controls LEDs, motor, and optional buzzer |
| **Green LED** | Indicates driver is active |
| **Red LED** | Indicates driver is drowsy |
| **DC Motor + Driver (L298N)** | Simulates vehicle motion |
| **Active Buzzer** | Optional secondary alert |
| **Webcam** | Captures driver’s face |
| **Power Supply** | 5V (NodeMCU), 5–12V (motor driver) |
| **Breadboard + Jumper Wires** | For prototyping connections |

---

## ⚡ Circuit Connections

| Component | NodeMCU Pin | Description |
|------------|-------------|-------------|
| Green LED | D1 (GPIO 5) | Anode → via 220Ω resistor |
| Red LED | D2 (GPIO 4) | Anode → via 220Ω resistor |
| Buzzer (Optional) | D3 (GPIO 0) | Positive pin |
| Motor IN | D5 (GPIO 14) | To motor driver input |
| GND | — | Common ground for all |

### 🧠 Notes:
- Always connect **NodeMCU GND** and **motor driver GND** together.  
- Use a **separate 5–12V supply** for the motor if possible.  
- Ensure LED resistors are used (~220Ω) to avoid burning pins.  

---

## 💻 Software Setup

### 🧠 Python (on PC)

#### Requirements
- Python 3.8+
- Required libraries:
  ```bash
  pip install opencv-python mediapipe numpy pyaudio requests
  #### 🏃‍♂️ Run the Project

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/Driver-Drowsiness-Detection-IoT.git
   cd Driver-Drowsiness-Detection-IoT

