#include "heartbeat.h"

Heartbeat::Heartbeat(unsigned long intervalMs) : _intervalMs(intervalMs) {}

bool Heartbeat::due(unsigned long nowMs) const {
    return nowMs - _lastSentMs >= _intervalMs;
}

void Heartbeat::markSent(unsigned long nowMs) {
    _lastSentMs = nowMs;
}
