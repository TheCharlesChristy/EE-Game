#pragma once
#include <Arduino.h>

/**
 * Protocol message type constants and C++ struct definitions.
 *
 * These mirror the JSON schemas in shared/schemas/v1/.
 * The top-level wire message fields (version, type, device_id, payload) and
 * all payload field names match the JSON Schema definitions exactly.
 * The protocol version must match PROTOCOL_VERSION in shared/constants/protocol.py.
 *
 * SRS reference: IF-001 to IF-006, Section 11.3.
 */

static constexpr char PROTOCOL_VERSION[] = "1";

// Message type string constants (match shared/constants/protocol.py MSG_* values)
static constexpr char MSG_REGISTER[]   = "register";
static constexpr char MSG_HEARTBEAT[]  = "heartbeat";
static constexpr char MSG_EVENT[]      = "event";
static constexpr char MSG_TEST_EVENT[] = "test_event";
static constexpr char MSG_STATE_TRANSITION[] = "state_transition";

/**
 * Payload for a device registration message (shared/schemas/v1/register.schema.json).
 * Sent once on first connection to the backend WebSocket.
 * Mirrors the "payload" object required fields: firmware_version, board_target.
 */
struct RegisterPayload {
    const char* firmware_version;  ///< Build-time version string
    const char* board_target;      ///< e.g. "esp32-c3" or "esp32dev"
};

/**
 * Payload for a heartbeat message (shared/schemas/v1/heartbeat.schema.json).
 * Sent periodically to maintain liveness status on the backend.
 * Mirrors the "payload" object required field: timestamp_ms.
 */
struct HeartbeatPayload {
    unsigned long timestamp_ms;  ///< Device uptime in milliseconds (millis())
};

struct EventPayload {
    const char* event_type;
    const char* dedupe_key;
    unsigned long timestamp_ms;
    unsigned long elapsed_ms;
    bool correct;
};

struct StateTransitionPayload {
    String round_id;
    String phase;
    String led_state;
    unsigned long remaining_ms;
};

/**
 * Full wire envelope for a register message.
 * Mirrors the top-level required fields: version, type, device_id, payload.
 */
struct RegisterMessage {
    const char*     version;    ///< Always PROTOCOL_VERSION
    const char*     type;       ///< Always MSG_REGISTER
    const char*     device_id;  ///< Stable hardware identifier (e.g. MAC address)
    RegisterPayload payload;
};

/**
 * Full wire envelope for a heartbeat message.
 * Mirrors the top-level required fields: version, type, device_id, payload.
 */
struct HeartbeatMessage {
    const char*      version;    ///< Always PROTOCOL_VERSION
    const char*      type;       ///< Always MSG_HEARTBEAT
    const char*      device_id;  ///< Stable hardware identifier (e.g. MAC address)
    HeartbeatPayload payload;
};

struct EventMessage {
    const char*  version;
    const char*  type;
    const char*  device_id;
    EventPayload payload;
};
