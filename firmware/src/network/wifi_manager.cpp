#include "wifi_manager.h"
#include <WiFi.h>

WiFiManager::WiFiManager(const char* ssid, const char* password)
    : _ssid(ssid), _password(password) {}

bool WiFiManager::connect(uint8_t maxAttempts) {
    Serial.printf("[WiFi] Connecting to '%s'...\n", _ssid);
    WiFi.begin(_ssid, _password);

    uint8_t attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < maxAttempts) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("[WiFi] Connected. IP: %s\n", WiFi.localIP().toString().c_str());
        return true;
    }
    Serial.println("[WiFi] Connection failed.");
    return false;
}

bool WiFiManager::isConnected() const {
    return WiFi.status() == WL_CONNECTED;
}

const char* WiFiManager::ipAddress() const {
    static String ip;
    ip = WiFi.localIP().toString();
    return ip.c_str();
}
