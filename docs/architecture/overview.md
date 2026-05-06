# Architecture Overview

This document describes the high-level architecture of the EE-Game platform. It is the primary entry point for developers joining the project and references the authoritative baseline in the Software Requirements Specification (SRS) v1.0, Section 5 (System Context and Logical Architecture).

## Top-level concerns

The platform is divided into five clearly separated concerns, each with its own directory and ownership rules:

| Directory | Concern | Primary technology |
| --- | --- | --- |
| `host/backend/` | Python API server, game engine, session manager, device registry, scoring service, WebSocket fan-out, SQLite persistence | Python 3.12+, FastAPI, asyncio, SQLite |
| `host/frontend/` | React web application serving both host-control mode and public-display mode | React 18+, TypeScript, Vite |
| `firmware/` | ESP32 device firmware: WiFi connection, device registration, heartbeat, LED state, game event publication | PlatformIO, Arduino framework for ESP32, C++ |
| `shared/` | Versioned JSON Schema message definitions and Python protocol constants; no runtime dependencies | JSON Schema draft-07, Python (constants only) |
| `docs/` | Architecture notes, protocol documentation, deployment runbooks, test evidence, SRS traceability | Markdown |

These boundaries are non-negotiable. Dependency direction rules are detailed in `docs/architecture/module-boundaries.md`.

## System topology

```
+------------------+         WiFi / WebSocket          +--------------------+
|  ESP32-C3 Device | ---------------------------------> |                    |
|  (up to 20)      |   ws://<host>:8000/ws/devices      |   Raspberry Pi 4   |
+------------------+                                    |                    |
                                                        |  Python Backend    |
+------------------+         WiFi / WebSocket          |  (FastAPI, asyncio)|
|  Browser Client  | <--------------------------------- |                    |
|  (host-control   |   ws://<host>:8000/ws/frontend     |  SQLite            |
|   or public      |                                    |  persistence       |
|   display)       |   http://<host>:8000/              |                    |
+------------------+                                    +--------------------+
```

All network communication is local. The Raspberry Pi provides or manages the local network; no internet connectivity is required or used at runtime (SRS Section 5.2).

## Single-authority principle

The backend is the sole authoritative owner of all game state, session state, scoring, timers, device registry, and persistence. Neither the frontend nor firmware may mutate authoritative state directly. All state changes flow through the backend and are then broadcast to subscribers.

This principle is fundamental to maintaining correctness under concurrent device activity and is required by SRS Section 5.3 (Concurrency Baseline). It means:

- The frontend subscribes to state; it never writes state except through explicit host-action API calls.
- Firmware devices publish events; the backend decides their effect on game or session state.
- All timers and countdowns run in the backend's asyncio event loop, not in the frontend or firmware.

## Technology stack

| Component | Technology | Rationale |
| --- | --- | --- |
| Backend runtime | Python 3.12+ | Locked in SRS Section 4 Fixed Design Decisions |
| Backend framework | FastAPI | Async-native, WebSocket support, typed, low overhead |
| Backend concurrency | asyncio (single event loop) | Required by SRS Section 5.3; no thread-per-device |
| Backend persistence | SQLite | Locked in SRS Section 4; offline, embedded, no server process |
| Frontend framework | React 18+ with TypeScript | Locked in SRS Section 4 |
| Frontend build tool | Vite | Fast local builds; compatible with Raspberry Pi serving |
| Firmware build system | PlatformIO | Locked in SRS Section 4 |
| Firmware framework | Arduino framework for ESP32 | Locked in SRS Section 4 |
| Default firmware target | ESP32-C3 | Locked in SRS Section 4 |
| Protocol format | JSON over WebSocket | Aligns with SRS IF-001–IF-006 |
| Schema language | JSON Schema draft-07 | Versioned, human-readable, toolable |

## Logical components

The following logical components correspond to the responsibilities listed in SRS Section 5.1:

| Component | Location | Responsibility |
| --- | --- | --- |
| Session Manager | `host/backend/core/session_manager.py` | Create, save, resume, pause, finish, and archive sessions (EP-02) |
| Player and Device Registry | `host/backend/core/device_registry.py` | Map devices to players, track connectivity and heartbeats (EP-03) |
| Game Engine | `host/backend/games/` | Load game definitions, run phase transitions, process events (EP-05, EP-06) |
| Scoring Service | `host/backend/core/scoring.py` | Cumulative totals, per-round scores, audit (EP-07) |
| Persistence Service | `host/backend/db/` | SQLite repository layer (EP-08) |
| Realtime Broadcaster | `host/backend/core/connection_manager.py` | WebSocket fan-out to frontends and devices (EP-01) |
| Host-Control UI | `host/frontend/src/` (host-control route) | Operator dashboard, game controls (EP-04) |
| Public Display UI | `host/frontend/src/` (public route) | Room-facing leaderboard and game state (EP-04) |
| Firmware | `firmware/src/` | WiFi, registration, heartbeat, LED, event publication (EP-09) |

## Dual frontend mode

The React application serves two distinct modes from a single build, determined by URL routing:

- `/host` — Host-control mode: full operator panel, session controls, diagnostics.
- `/display` — Public-display mode: room-facing leaderboard and game state.

Both modes consume the same WebSocket push channel (`/ws/frontend`) and render different views of the same authoritative state. This is defined in EP-04 and UI requirements UI-001–UI-016 of the SRS.

## Further reading

- `docs/architecture/module-boundaries.md` — Ownership rules and allowed dependency directions.
- `docs/architecture/websocket-protocol.md` — Wire protocol message types and connection lifecycle.
- `docs/architecture/srs-traceability.md` — Mapping from SRS requirement IDs to implementing components.
- SRS v1.0, Section 5 — System Context and Logical Architecture (authoritative reference).
- SRS v1.0, Appendix A — Recommended Repository Structure.
