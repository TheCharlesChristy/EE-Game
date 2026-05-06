# WebSocket Protocol

This document defines the EP-01 WebSocket protocol used by the EE-Game platform. It covers the two WebSocket endpoints, the message envelope format, the EP-01 message type catalogue, error handling, reconnect strategy, and concurrency design.

References: SRS v1.0 Section 5.2 (Networking Baseline), Section 5.3 (Concurrency Baseline), IF-001 through IF-006.

## WebSocket endpoints

The backend exposes two WebSocket endpoints on port 8000:

| Endpoint | Clients | Purpose |
| --- | --- | --- |
| `ws://<host>:8000/ws/devices` | ESP32 devices | Device registration, heartbeat, and game event ingress |
| `ws://<host>:8000/ws/frontend` | Browser clients (host-control and public-display modes) | Authoritative state push from backend to UI |

Both endpoints are served by the same FastAPI application process and share the same asyncio event loop. The host address is the Raspberry Pi's IP on the local host-managed network.

## Message envelope

All messages on both endpoints use a JSON envelope with the following top-level fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `version` | string | Yes | Protocol version. Currently `"1"`. Defined in `shared/constants/protocol.py` as `PROTOCOL_VERSION`. |
| `type` | string | Yes | Message type identifier. See the type catalogue below. |
| `device_id` | string | No | Stable hardware identifier of the sending device. Required on device-originating messages; absent on backend-to-frontend messages. |
| `payload` | object | Yes | Message-specific data. Structure varies by type; defined in `shared/schemas/v1/`. |

The full field-level constraints for each message type are defined in the JSON Schema files under `shared/schemas/v1/`. Those schemas are the authoritative source of truth; this document provides human-readable context.

## EP-01 message type catalogue

### `register` — Device → Backend

Sent by an ESP32 device immediately after establishing its WebSocket connection to `/ws/devices`. The backend uses this message to create or restore the device's entry in the device registry.

Schema: `shared/schemas/v1/register.schema.json`

| Payload field | Type | Description |
| --- | --- | --- |
| `firmware_version` | string | The firmware build version string. |
| `board_target` | string | The PlatformIO environment target name (e.g. `esp32c3`). |

### `heartbeat` — Device → Backend

Sent periodically by a registered device to signal liveness. The backend updates the device's `last_seen_at` timestamp on receipt. Devices that miss the heartbeat threshold transition to `stale` and eventually `disconnected` connection state.

Schema: `shared/schemas/v1/heartbeat.schema.json`

| Payload field | Type | Description |
| --- | --- | --- |
| `timestamp_ms` | integer (≥ 0) | Device uptime in milliseconds since last boot. |

### `state_update` — Backend → Frontend

Pushed by the backend to all subscribed frontend clients when authoritative state changes. Frontend clients must not rely on polling; all live state arrives through this message type.

Schema: `shared/schemas/v1/state_update.schema.json`

| Payload field | Type | Description |
| --- | --- | --- |
| `event` | string | The state event name. Examples: `device_registered`, `device_disconnected`, `session_started`, `round_state_changed`. |
| `data` | object | Event-specific payload. Structure varies by event name; defined per event in EP-02 through EP-09 implementation. |

### `device_list` — Backend → Frontend

Pushed by the backend to a newly connected frontend client on initial connection, and whenever the connected device set changes materially. Provides the complete current device and player state so clients can render without waiting for incremental events.

Payload: an array of device/player state objects. Schema to be finalised in EP-03.

### `error` — Backend → Client (either endpoint)

Sent by the backend when a received message cannot be processed. The connection is preserved; the error is informational.

```json
{
  "version": "1",
  "type": "error",
  "payload": {
    "code": "UNKNOWN_TYPE",
    "message": "Received message type 'foo' is not recognised by this server."
  }
}
```

| Error code | Meaning |
| --- | --- |
| `UNKNOWN_TYPE` | The `type` field in the received message is not recognised. |
| `VALIDATION_FAILED` | The message did not conform to the expected JSON Schema. |
| `NOT_REGISTERED` | A device sent a non-register message before completing registration. |

## Error handling

When the backend receives a message it cannot process:

1. The error is logged at WARNING level with the raw message and connection identifier.
2. An `error` message is sent back to the originating connection.
3. The connection is preserved; no disconnect is forced for a single bad message.
4. If a device sends repeated malformed messages in a short window, the backend may close the connection after logging at ERROR level.

This behaviour satisfies SRS IF-003 (validation failures handled gracefully) and IF-004 (malformed messages do not destabilise the host session).

## Reconnect strategy

**Device reconnect:** Devices that lose their connection implement exponential backoff before retrying. Minimum retry interval is 1 second; maximum is 30 seconds. On reconnect, the device sends a fresh `register` message. The backend attempts to restore the existing device-player mapping by matching `device_id` (SRS FR-029).

**Frontend reconnect:** Browser clients that lose the WebSocket connection implement exponential backoff before retrying. On reconnect, the backend sends a `device_list` message and any pending `state_update` messages to resynchronise the client's view. Clients must not assume their local state is valid across a reconnect gap.

**Backend-side tracking:** The backend tracks each connection's last activity timestamp. Connections that exceed the stale threshold without a heartbeat are marked `stale`; those that exceed the disconnect threshold are marked `disconnected` and removed from the active registry.

## Concurrency design

The backend uses a single asyncio event loop for all networking, timer management, and state mutation (SRS Section 5.3). Key design rules:

- All WebSocket connection handling, device event processing, and frontend fan-out run as asyncio coroutines on the same event loop.
- The `ConnectionManager` class (implemented in `host/backend/core/connection_manager.py`) holds the registry of active connections and uses `asyncio.Lock` to serialise writes to shared connection state.
- Game timers are asyncio tasks, not threads. They schedule callbacks through the event loop rather than blocking.
- Blocking operations (e.g. SQLite writes, file I/O) are dispatched to a thread pool executor via `asyncio.get_event_loop().run_in_executor()` to prevent event loop stall.
- No correctness guarantee depends on a thread-per-device model. All authoritative state transitions are serialised through the event loop.

This design directly satisfies NFR-001 through NFR-005 (performance and non-blocking operation) and NFR-006 through NFR-010 (reliability and graceful degradation).

## Protocol versioning

All messages carry a `version` field (currently `"1"`). The backend rejects messages whose version it does not support with an `error` response carrying code `VALIDATION_FAILED`. When a breaking protocol change is required, a new version is introduced and both versions are supported simultaneously during a transition period. Versioning rules are defined in `shared/README.md`.
