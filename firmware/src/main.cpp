/**
 * EE-Game firmware entry point.
 *
 * Setup sequence per SRS Section 8.3 (Device Lifecycle):
 *   1. Boot LED state
 *   2. Serial init (debug output)
 *   3. Load board config
 *   4. WiFi connect (CONNECTING LED state)
 *   5. Register with backend (CONNECTED LED state on success)
 *   6. Enter main loop: heartbeat + LED update
 *
 * Full protocol implementation: EP-09.
 */

#include <Arduino.h>
#include <WiFi.h>
#include "config/board_config.h"
#include "input/input_manager.h"
#include "led/led_manager.h"
#include "network/wifi_manager.h"
#include "network/ws_client.h"
#include "protocol/heartbeat.h"
#include "protocol/message_types.h"

// --- Configuration ---
// In production these come from a secrets header or OTA config; for scaffolding
// they are compile-time defaults. Never commit real credentials.
#ifndef WIFI_SSID
  #define WIFI_SSID "ee-game"
#endif
#ifndef WIFI_PASSWORD
  #define WIFI_PASSWORD "changeme"
#endif
#ifndef BACKEND_HOST
  #define BACKEND_HOST "192.168.4.1"
#endif
#ifndef BACKEND_PORT
  #define BACKEND_PORT 8000
#endif
#ifndef FIRMWARE_VERSION
  #define FIRMWARE_VERSION "dev"
#endif

static LedManager ledManager(STATUS_LED_PIN, STATUS_LED_ACTIVE);
static WiFiManager wifiManager(WIFI_SSID, WIFI_PASSWORD);
static EeWebSocketClient wsClient;
static Heartbeat heartbeat(5000);
static InputManager inputManager(INPUT_BUTTON_PIN, INPUT_ANALOG_PIN);
static String deviceId;

static const char* boardTarget() {
#ifdef BOARD_ESP32C3
    return "esp32-c3";
#elif defined(BOARD_ESP32DEV)
    return "esp32dev";
#else
    return "unknown";
#endif
}

void setup() {
    Serial.begin(115200);
    Serial.println("[EE-Game] Firmware starting");

    ledManager.begin();
    inputManager.begin();
    ledManager.setState(LedState::BOOT);
    delay(500);

    ledManager.setState(LedState::CONNECTING);
    bool connected = wifiManager.connect();

    if (connected) {
        deviceId = WiFi.macAddress();
        deviceId.replace(":", "");
        deviceId.toLowerCase();
        ledManager.setState(LedState::CONNECTING);
        wsClient.begin(BACKEND_HOST, BACKEND_PORT, deviceId.c_str(), &ledManager);
        Serial.printf("[EE-Game] Device id %s firmware %s\n", deviceId.c_str(), FIRMWARE_VERSION);
    } else {
        ledManager.setState(LedState::TEST_FAULT);
        Serial.println("[EE-Game] WiFi failed — will retry in loop");
    }
}

void loop() {
    ledManager.update();
    wsClient.loop();

    if (!wifiManager.isConnected()) {
        ledManager.setState(LedState::CONNECTING);
        if (wifiManager.connect(10)) {
            if (deviceId.length() == 0) {
                deviceId = WiFi.macAddress();
                deviceId.replace(":", "");
                deviceId.toLowerCase();
            }
            wsClient.begin(BACKEND_HOST, BACKEND_PORT, deviceId.c_str(), &ledManager);
        }
        return;
    }

    unsigned long now = millis();
    if (heartbeat.due(now)) {
        wsClient.sendHeartbeat(now);
        heartbeat.markSent(now);
    }

    EventPayload event;
    if (inputManager.poll(event)) {
        wsClient.sendEvent(event, false);
    }
}
