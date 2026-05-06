# SRS Traceability Matrix

This document maps SRS v1.0 requirement identifiers to the implementing components, files, and epics in the EE-Game repository. It is the primary artefact for demonstrating requirements coverage during review and acceptance testing.

The SRS baseline document is `docs/electronic_engineering_game_SRS_v1.md`. All requirement IDs below refer to that document.

## Non-Functional Requirements — Maintainability (Section 7.4)

| SRS ID | Requirement summary | Implementing component / file | Epic |
| --- | --- | --- | --- |
| NFR-016 | Codebase shall separate host backend, host frontend, firmware, shared protocol, and documentation concerns | `host/backend/`, `host/frontend/`, `firmware/`, `shared/`, `docs/` — enforced by module boundary rules in `docs/architecture/module-boundaries.md` | EP-01 |
| NFR-017 | Board-specific firmware configuration shall be isolated from common gameplay logic | `firmware/src/config/board_config.h` (board-specific pin mappings and feature switches) | EP-01, EP-09 |
| NFR-018 | New games shall be addable without modifying core infrastructure beyond defined integration points | `host/backend/games/` game interface definition; game contract per SRS Section 12.1 | EP-05 |
| NFR-019 | Protocol messages and key domain models shall be documented | `shared/schemas/v1/`, `docs/architecture/websocket-protocol.md`, `shared/README.md` | EP-01 |
| NFR-020 | Builds for host software and firmware shall be reproducible | `host/backend/pyproject.toml`, `host/frontend/package.json`, `firmware/platformio.ini` | EP-01 |

## Non-Functional Requirements — Performance (Section 7.1)

| SRS ID | Requirement summary | Implementing component / file | Epic |
| --- | --- | --- | --- |
| NFR-001 | Support 20 concurrently connected player devices | `host/backend/core/connection_manager.py` — asyncio-based connection registry | EP-01 |
| NFR-002 | Normal gameplay interactions shall feel near real time | `host/backend/core/connection_manager.py` — single event loop, no per-device threads | EP-01 |
| NFR-003 | Host actions shall remain responsive while device events are being processed | `host/backend/core/connection_manager.py` — asyncio task scheduling | EP-01 |
| NFR-004 | Public display shall update smoothly for timed and reactive games | `host/backend/core/connection_manager.py` fan-out; `host/frontend/` WebSocket subscription | EP-01, EP-04 |
| NFR-005 | Blocking operations shall not freeze the core event loop | `host/backend/` — blocking I/O dispatched via `run_in_executor()`; no synchronous DB calls on event loop | EP-01 |

## Non-Functional Requirements — Reliability (Section 7.2)

| SRS ID | Requirement summary | Implementing component / file | Epic |
| --- | --- | --- | --- |
| NFR-006 | System shall surface device disconnects and stale connections clearly | `host/backend/core/heartbeat.py`, `host/backend/api/ws/` — stale timeout tracking | EP-01, EP-03 |
| NFR-007 | System shall preserve saved sessions across normal application restarts | `host/backend/db/` SQLite persistence; `host/backend/core/session_manager.py` | EP-02, EP-08 |
| NFR-008 | Persistence design shall minimise risk of session corruption | `host/backend/db/` — transactional writes, repository pattern | EP-08 |
| NFR-009 | System shall degrade gracefully when a device misbehaves or sends malformed data | `host/backend/api/ws/` — message validation, error response, connection preservation (see `docs/architecture/websocket-protocol.md`) | EP-01 |
| NFR-010 | Host shall recover control after common faults without ending the session | `host/backend/core/session_manager.py`; `docs/deployment/` recovery runbook | EP-01, EP-02 |

## Technical Acceptance Criteria (Section 15.2)

| SRS ID | Requirement summary | Implementing component / file | Epic |
| --- | --- | --- | --- |
| AC-011 | Host software runs on Raspberry Pi 4 Model B or better | `docs/deployment/` — Pi deployment runbooks (EP-01-US-03) | EP-01 |
| AC-012 | Persistence uses SQLite | `host/backend/db/` | EP-08 |
| AC-013 | Firmware builds with PlatformIO using Arduino framework for ESP32 | `firmware/platformio.ini` | EP-09 |
| AC-014 | Default firmware target is ESP32-C3 | `firmware/platformio.ini` — default environment | EP-09 |
| AC-015 | Retargeting to another ESP32-family board requires only environment selection and limited board-specific adaptation | `firmware/src/config/board_config.h`; PlatformIO environment configuration | EP-09 |

## Internal Protocol Requirements (Section 11.3)

| SRS ID | Requirement summary | Implementing component / file | Epic |
| --- | --- | --- | --- |
| IF-001 | Protocol messages shall be versioned | `shared/schemas/v1/` — version field in all schemas; `shared/constants/protocol.py` `PROTOCOL_VERSION` | EP-01 |
| IF-002 | Protocol shall support registration, heartbeat, state transition, event reporting, and error signalling | `shared/schemas/v1/register.schema.json`, `heartbeat.schema.json`, `state_update.schema.json`; error type in `docs/architecture/websocket-protocol.md` | EP-01 |
| IF-003 | Message validation failures shall be handled gracefully | `host/backend/api/ws/` — validation on receipt, error response sent, connection preserved | EP-01 |
| IF-004 | Malformed device messages shall not destabilise the host session | `host/backend/api/ws/` — exception isolation per connection | EP-01 |
| IF-005 | Shared message schemas shall be documented in the repository | `shared/schemas/v1/`, `shared/README.md`, `docs/architecture/websocket-protocol.md` | EP-01 |
| IF-006 | Protocol shall allow backend to correlate messages with a stable device identity | `device_id` field in all device-originating schemas; `shared/schemas/v1/register.schema.json` | EP-01, EP-03 |

## Functional Requirements — Session Management (Section 6.1)

| SRS ID | Requirement summary | Implementing component / file | Epic |
| --- | --- | --- | --- |
| FR-001–010 | Full session lifecycle: create, resume, save, pause, finish, archive, single active session | `host/backend/core/session_manager.py`, `host/backend/db/` | EP-02 |

## Functional Requirements — Device Management (Section 6.3)

| SRS ID | Requirement summary | Implementing component / file | Epic |
| --- | --- | --- | --- |
| FR-021–030 | Device registry: up to 20 devices, liveness, stable identity, reconnect mapping, unknown device handling | `host/backend/core/device_registry.py`, `host/backend/core/heartbeat.py`, `host/backend/api/ws/` | EP-03 |

## Functional Requirements — Game Catalogue (Section 6.4)

| SRS ID | Requirement summary | Implementing component / file | Epic |
| --- | --- | --- | --- |
| FR-031–040 | 10–15 built-in games, game metadata, filtering, solo/team support | `host/backend/games/`, `host/backend/core/game_engine.py` | EP-05 |

## Open design decisions

The following items are noted in the SRS and epic documentation but remain as design decisions to be resolved during implementation. They are deferred rather than forgotten:

- **Exact Raspberry Pi OS baseline**: The SRS specifies Raspberry Pi 4 Model B as minimum hardware but does not prescribe a specific OS image version. The deployment runbook (`docs/deployment/`) will record the tested baseline when EP-01-US-03 is completed.
- **Venue RF configuration**: SRS Section 3.3 acknowledges variable RF conditions in venue environments. The specific local network topology (whether the Pi acts as a WiFi access point or joins an existing network) is a deployment configuration choice not locked in the SRS. This will be documented in `docs/deployment/` when deployment baseline work is completed.
- **Latency budget numbers**: SRS NFR-001 through NFR-005 specify responsiveness qualitatively (near real time, smooth updates) without numeric thresholds. Specific latency budget values will be established during EP-01-T03 load and fault testing and recorded in `docs/test-evidence/`.
