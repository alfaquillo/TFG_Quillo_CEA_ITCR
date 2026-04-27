#include "ws_server.h"
#include <ArduinoJson.h>
#include "led_status.hpp"
#include "Ticker.h"

/* ----------- WebSocket ----------- */
WebSocketsServer ws = WebSocketsServer(8765);

uint8_t client_num = 0xFF;
bool ws_connected = false;

/* ----------- Estado ----------- */
WS_STATE ws_state = DISCONNECTED;

/* ----------- Info ----------- */
String ws_name = "";
String ws_type = "";
String ws_check = "SC";
String videoUrl = "";

/* ----------- Timing ----------- */
Ticker timer;

uint32_t lastPingSent = 0;
uint32_t lastPongReceived = 0;
uint32_t last_valid_cmd_time = 0;

uint32_t last_process_time = 0;
uint32_t last_send_time = 0;

const uint32_t PING_INTERVAL = 5000;

/* ----------- Secuencia ----------- */
uint32_t last_seq = 0;

/* ----------- Utils ----------- */
String intToString(uint8_t * value, size_t length) {
  String buf;
  for (size_t i = 0; i < length; i++){
    buf += (char)value[i];
  }
  return buf;
}

/* ----------- STOP seguro ----------- */
void sendSTOP() {
  Serial.println("WS+0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0");
}

/* ----------- Supervisión ----------- */
void supervisionTask() {
  uint32_t now = millis();

  /* ---- Heartbeat ---- */
  if (ws_connected && client_num != 0xFF) {

    if (now - lastPingSent > PING_INTERVAL) {
      StaticJsonDocument<64> ping;
      ping["ping"] = now;

      String out;
      serializeJson(ping, out);
      ws.sendTXT(client_num, out);

      lastPingSent = now;
    }

    if (now - lastPongReceived > TIMEOUT) {
      Serial.println("[DISCONNECTED] timeout (no pong)");

      ws.disconnect(client_num);
      ws_connected = false;
      client_num = 0xFF;

      ws_state = DISCONNECTED;
      sendSTOP();
    }
  }

  /* ---- Timeout de comandos ---- */
  if (ws_state == VALID_STREAM) {
    if (now - last_valid_cmd_time > CMD_TIMEOUT) {
      Serial.println("[STALE] command timeout");

      ws_state = STALE;
      sendSTOP();
    }
  }
}

/* ----------- Clase ----------- */
WS_Server::WS_Server() {}

void WS_Server::close() {
  ws_connected = false;
  client_num = 0xFF;
  ws_state = DISCONNECTED;
  ws.close();
}

void WS_Server::begin(int port, String _name, String _type, String _check) {
  ws_name = _name;
  ws_type = _type;
  ws_check = _check;

  ws.begin();
  ws.onEvent([](uint8_t cn, WStype_t type, uint8_t * payload, size_t length) {

    client_num = cn;

    switch(type) {

      case WStype_CONNECTED: {
        LED_STATUS_CONNECTED();

        IPAddress remoteIp = ws.remoteIP(client_num);
        Serial.print("[CONNECTED] ");
        Serial.println(remoteIp.toString());

        String check_info = "{\"Name\":\"" + ws_name
                          + "\",\"Type\":\"" + ws_type
                          + "\",\"Check\":\"" + ws_check
                          + "\",\"video\":\"" + videoUrl
                          + "\"}";

        ws.sendTXT(client_num, check_info);

        ws_connected = true;
        ws_state = STALE;

        uint32_t now = millis();
        lastPingSent = now;
        lastPongReceived = now;
        last_valid_cmd_time = now;

        break;
      }

      case WStype_DISCONNECTED: {
        LED_STATUS_DISCONNECTED();

        Serial.println("[DISCONNECTED] client");

        ws_connected = false;
        client_num = 0xFF;
        ws_state = DISCONNECTED;

        sendSTOP();
        break;
      }

      case WStype_TEXT: {

        String incoming = intToString(payload, length);
        if (incoming.length() == 0) return;

        DynamicJsonDocument recvBuffer(WS_BUFFER_SIZE);
        DeserializationError err = deserializeJson(recvBuffer, incoming);

        if (err) {
          Serial.println("[WS] JSON corrupto descartado");
          return;
        }

        uint32_t now = millis();
        lastPongReceived = now;

        /* ---- PONG ---- */
        if (recvBuffer.containsKey("pong")) return;

        /* ---- PING ---- */
        if (recvBuffer.containsKey("ping")) {
          StaticJsonDocument<64> pong;
          pong["pong"] = now;

          String out;
          serializeJson(pong, out);
          ws.sendTXT(client_num, out);
          return;
        }

        /* ---- SEQ ---- */
        if (recvBuffer.containsKey("seq")) {
          uint32_t seq = recvBuffer["seq"];
          if (seq <= last_seq) return;
          last_seq = seq;
        }

        /* ---- Anti flood ---- */
        if (now - last_process_time < MIN_PROCESS_INTERVAL) return;
        last_process_time = now;

        /* ---- Construcción segura ---- */
        String result = "WS+";
        bool hasData = false;

        for (int i = 0; i < REGIONS_LENGTH; i++) {

          char key[2] = { REGIONS[i], '\0' };

          if (recvBuffer.containsKey(key)) {

            String value;

            if (recvBuffer[key].is<JsonArray>()) {
              JsonArray arr = recvBuffer[key];
              for (JsonVariant v : arr) {
                value += v.as<String>();
                value += ",";
              }
              if (value.length() > 0) value.remove(value.length() - 1);
            } else {
              value = recvBuffer[key].as<String>();
            }

            if (value == "true") value = "1";
            else if (value == "false") value = "0";

            if (value.length() > 0 && value != "null") {
              hasData = true;
              result += value;
            }
          }

          if (i != REGIONS_LENGTH - 1) result += ';';
        }

        if (!hasData) return;

        /* ---- ACTUALIZAR ESTADO ---- */
        last_valid_cmd_time = now;
        ws_state = VALID_STREAM;

        /* ---- SOLO enviar si stream válido ---- */
        if (ws_state == VALID_STREAM) {
          if (now - last_send_time > SEND_INTERVAL) {
            Serial.println(result);
            last_send_time = now;
          }
        }

        break;
      }

      case WStype_BIN: {
        lastPongReceived = millis();
        break;
      }

      case WStype_ERROR: {
        LED_STATUS_ERROOR();
        break;
      }

      default:
        break;
    }
  });

  timer.attach_ms(100, supervisionTask);
}

void WS_Server::loop() {
  ws.loop();
}

void WS_Server::send(String data) {
  if (!ws_connected || client_num == 0xFF) return;
  if (data.length() == 0) return;

  for (size_t i = 0; i < data.length(); i++) {
    if (data[i] < 9 || data[i] > 126) return;
  }

  ws.sendTXT(client_num, data);
}

void WS_Server::sendBIN(uint8_t* payload, size_t length) {
  if (!ws_connected || client_num == 0xFF) return;
  ws.sendBIN(client_num, payload, length);
}

bool WS_Server::is_connected() {
  return ws_connected;
}