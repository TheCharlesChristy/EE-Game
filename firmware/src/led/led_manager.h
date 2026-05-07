#pragma once
#include <Arduino.h>

/**
 * LED state names as defined in shared/constants/protocol.py (LED_* constants).
 * These must remain in sync with the backend's LED state model.
 */
enum class LedState {
    BOOT,          ///< Device booting up
    CONNECTING,    ///< Searching for WiFi — no network connection
    CONNECTING_WS, ///< WiFi connected, WebSocket handshake in progress
    CONNECTED,     ///< Registered with backend, idle
    TEST_FAULT,    ///< Test phase failure or circuit fault
    LIVE,          ///< Active gameplay
};

/**
 * Manages the status LED using simple on/off patterns.
 * More complex patterns (blink rates per state) are implemented in apply().
 */
class LedManager {
public:
    explicit LedManager(uint8_t pin, uint8_t activeLevel = HIGH);

    void begin();
    void setState(LedState state);
    void update();  ///< Call every loop() iteration for timed blink patterns.

private:
    uint8_t _pin;
    uint8_t _activeLevel;
    LedState _state = LedState::BOOT;
    unsigned long _lastToggleMs = 0;
    bool _ledOn = false;

    void setPin(bool on);
    unsigned long blinkIntervalMs() const;
};
