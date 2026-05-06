#pragma once
#include <Arduino.h>
#include "message_types.h"

class MessageCodec {
public:
    static String encodeRegister(const char* deviceId, const char* firmwareVersion, const char* boardTarget);
    static String encodeHeartbeat(const char* deviceId, unsigned long timestampMs);
    static String encodeEvent(const char* deviceId, const EventPayload& payload, bool testEvent = false);
    static bool decodeStateTransition(const String& text, StateTransitionPayload& out);
};
