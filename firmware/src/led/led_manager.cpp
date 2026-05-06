#include "led_manager.h"

LedManager::LedManager(uint8_t pin, uint8_t activeLevel)
    : _pin(pin), _activeLevel(activeLevel) {}

void LedManager::begin() {
    pinMode(_pin, OUTPUT);
    setPin(false);
}

void LedManager::setState(LedState state) {
    _state = state;
    _lastToggleMs = millis();
    _ledOn = false;
}

void LedManager::update() {
    unsigned long interval = blinkIntervalMs();
    if (interval == 0) {
        // Solid on for CONNECTED and LIVE states
        setPin(true);
        return;
    }
    if (millis() - _lastToggleMs >= interval) {
        _ledOn = !_ledOn;
        setPin(_ledOn);
        _lastToggleMs = millis();
    }
}

void LedManager::setPin(bool on) {
    digitalWrite(_pin, on ? _activeLevel : !_activeLevel);
}

unsigned long LedManager::blinkIntervalMs() const {
    switch (_state) {
        case LedState::BOOT:        return 500;   // slow blink: booting
        case LedState::CONNECTING:  return 200;   // fast blink: searching
        case LedState::CONNECTED:   return 0;     // solid: ready
        case LedState::TEST_FAULT:  return 100;   // very fast: error
        case LedState::LIVE:        return 0;     // solid: in game
        default:                    return 500;
    }
}
