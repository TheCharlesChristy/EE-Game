#include "input_manager.h"

InputManager::InputManager(uint8_t buttonPin, uint8_t analogPin)
    : _buttonPin(buttonPin), _analogPin(analogPin) {}

void InputManager::begin() {
    pinMode(_buttonPin, INPUT_PULLUP);
}

bool InputManager::poll(EventPayload& out) {
    bool current = digitalRead(_buttonPin);
    unsigned long now = millis();
    if (_lastButtonState == HIGH && current == LOW && now - _lastEventMs > 60) {
        _sequence++;
        snprintf(_dedupeKey, sizeof(_dedupeKey), "fw-%lu-%lu", now, _sequence);
        out.event_type = "button";
        out.dedupe_key = _dedupeKey;
        out.timestamp_ms = now;
        out.elapsed_ms = now - _lastEventMs;
        out.correct = true;
        _lastEventMs = now;
        _lastButtonState = current;
        return true;
    }
    _lastButtonState = current;
    return false;
}
