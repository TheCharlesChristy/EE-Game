#pragma once
#include <Arduino.h>

/**
 * Manages WiFi connection to the host-managed local network.
 * SRS reference: Section 5.2 (Networking Baseline), Section 8.3 (Device Lifecycle).
 *
 * Full implementation: EP-09.
 * Stub behaviour: connect to SSID/password from compile-time config, retry on failure.
 */
class WiFiManager {
public:
    WiFiManager(const char* ssid, const char* password);

    /**
     * Attempt to connect. Blocks until connected or maxAttempts exceeded.
     * @return true if connected successfully.
     */
    bool connect(uint8_t maxAttempts = 20);

    bool isConnected() const;

    const char* ipAddress() const;

private:
    const char* _ssid;
    const char* _password;
};
