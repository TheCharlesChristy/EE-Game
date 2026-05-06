#pragma once
#include <Arduino.h>

class Heartbeat {
public:
    explicit Heartbeat(unsigned long intervalMs = 5000);
    bool due(unsigned long nowMs) const;
    void markSent(unsigned long nowMs);

private:
    unsigned long _intervalMs;
    unsigned long _lastSentMs = 0;
};
