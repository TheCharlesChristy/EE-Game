#pragma once
#include <Arduino.h>
#include "../protocol/message_types.h"

class InputManager {
public:
    InputManager(uint8_t buttonPin, uint8_t analogPin);
    void begin();
    bool poll(EventPayload& out);

private:
    uint8_t _buttonPin;
    uint8_t _analogPin;
    bool _lastButtonState = HIGH;
    unsigned long _lastEventMs = 0;
    unsigned long _sequence = 0;
    char _dedupeKey[40] = {0};
};
