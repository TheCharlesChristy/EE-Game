#include "message_codec.h"
#include <ArduinoJson.h>

String MessageCodec::encodeRegister(const char* deviceId, const char* firmwareVersion, const char* boardTarget) {
    JsonDocument doc;
    doc["version"] = PROTOCOL_VERSION;
    doc["type"] = MSG_REGISTER;
    doc["device_id"] = deviceId;
    doc["payload"]["firmware_version"] = firmwareVersion;
    doc["payload"]["board_target"] = boardTarget;
    String output;
    serializeJson(doc, output);
    return output;
}

String MessageCodec::encodeHeartbeat(const char* deviceId, unsigned long timestampMs) {
    JsonDocument doc;
    doc["version"] = PROTOCOL_VERSION;
    doc["type"] = MSG_HEARTBEAT;
    doc["device_id"] = deviceId;
    doc["payload"]["timestamp_ms"] = timestampMs;
    String output;
    serializeJson(doc, output);
    return output;
}

String MessageCodec::encodeEvent(const char* deviceId, const EventPayload& payload, bool testEvent) {
    JsonDocument doc;
    doc["version"] = PROTOCOL_VERSION;
    doc["type"] = testEvent ? MSG_TEST_EVENT : MSG_EVENT;
    doc["device_id"] = deviceId;
    doc["payload"]["event_type"] = payload.event_type;
    doc["payload"]["dedupe_key"] = payload.dedupe_key;
    doc["payload"]["timestamp_ms"] = payload.timestamp_ms;
    doc["payload"]["elapsed_ms"] = payload.elapsed_ms;
    doc["payload"]["correct"] = payload.correct;
    String output;
    serializeJson(doc, output);
    return output;
}

bool MessageCodec::decodeStateTransition(const String& text, StateTransitionPayload& out) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, text);
    if (err) return false;
    if (doc["version"] != PROTOCOL_VERSION) return false;
    if (doc["type"] != MSG_STATE_TRANSITION) return false;
    JsonObject payload = doc["payload"];
    out.round_id = payload["round_id"] | "";
    out.phase = payload["phase"] | "";
    out.led_state = payload["led_state"] | "";
    out.remaining_ms = payload["remaining_ms"] | 0;
    return true;
}
