# shared/

This directory is the single source of truth for all cross-cutting protocol definitions, message schemas, and constants used by the EE-Game platform. Its purpose is to ensure that the backend, firmware, and any future tooling remain aligned on message structure and named values without duplicating definitions or coupling modules directly to each other.

## What belongs here

- **`schemas/`** — JSON Schema draft-07 files defining every wire-protocol message exchanged between ESP32 devices and the backend, and between the backend and browser frontends.
- **`constants/`** — Python constants for protocol version strings, message type names, and connection state values. These are imported by `host/backend/` only; firmware mirrors these values in C++ headers.

Nothing in this directory has runtime dependencies. It must remain importable without installing any third-party packages.

## Adding a new schema

Protocol schemas are versioned by directory. The current version is `v1`.

**Non-breaking additions** (new optional fields, new message types) may be added to `shared/schemas/v1/` with a corresponding update to this README.

**Breaking changes** (removed fields, changed field types, new required fields on existing messages, semantic changes to existing event types) require a new version directory:

1. Create `shared/schemas/v2/` and copy all relevant schemas from `v1/`.
2. Apply the breaking change only in `v2/`.
3. Update `shared/constants/protocol.py` to add a `PROTOCOL_VERSION_V2 = "2"` constant.
4. Document the migration path in `docs/architecture/websocket-protocol.md`.
5. Update the schema table in this README.

Both version directories may coexist while the backend supports a transition period. Remove an old version only when all firmware and clients have migrated.

## Current schemas

| File | Message type | Direction | Purpose |
| --- | --- | --- | --- |
| `schemas/v1/register.schema.json` | `register` | Device → Backend | ESP32 device registers its stable identity and firmware metadata on first connection. |
| `schemas/v1/heartbeat.schema.json` | `heartbeat` | Device → Backend | Periodic liveness signal sent by a registered device; carries device uptime in milliseconds. |
| `schemas/v1/state_update.schema.json` | `state_update` | Backend → Frontend | Backend pushes authoritative state change events to subscribed browser clients. |

## Importing constants in backend code

All backend code must import protocol constants from `shared/constants/protocol.py` rather than hardcoding strings. Example:

```python
from shared.constants.protocol import MSG_REGISTER, PROTOCOL_VERSION, CONN_CONNECTED
```

The `shared/constants/` package has no third-party dependencies and may be imported anywhere in `host/backend/` without side effects.

## Firmware mirror

Firmware C++ code cannot import Python modules. The `firmware/src/protocol/` directory contains C++ header files that mirror the constants and schema field names defined here. When a protocol constant changes in `shared/constants/protocol.py`, the corresponding C++ header in `firmware/src/protocol/` must be updated to match in the same commit. The JSON Schema files in `shared/schemas/` serve as the canonical reference for both sides.
