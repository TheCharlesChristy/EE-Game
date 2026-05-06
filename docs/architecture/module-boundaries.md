# Module Boundaries and Dependency Rules

This document defines ownership and permitted dependency directions for every top-level module in the EE-Game monorepo. It enforces SRS NFR-016 (codebase separation), NFR-018 (extensibility without broad rewrites), and NFR-019 (documented contracts).

Violating these rules creates coupling that undermines maintainability, makes game additions riskier, and breaks the single-authority principle described in `docs/architecture/overview.md`.

## Ownership and dependency table

| Module | Owns | May import from | Must NOT import from |
| --- | --- | --- | --- |
| `host/backend/` | All authoritative state; timers; scoring; WebSocket fan-out to frontends and devices; SQLite persistence; session and device lifecycle | `shared/constants/` | `host/frontend/`, `firmware/` |
| `host/frontend/` | UI rendering; user input handling; WebSocket client subscription and local view state | Nothing from other modules — consumes JSON messages from the WebSocket only | `host/backend/` modules directly; `firmware/`; `shared/constants/` |
| `firmware/` | Device I/O; WiFi connection management; event publication; LED state; heartbeat | Nothing from host — protocol field names and values are defined in `shared/schemas/` and mirrored in `firmware/src/protocol/` C++ headers | `host/backend/`, `host/frontend/` |
| `shared/` | Protocol schemas (`schemas/`) and Python constants (`constants/`) | Nothing — no runtime dependencies of any kind | `host/backend/`, `host/frontend/`, `firmware/` |
| `docs/` | Architecture documentation, deployment runbooks, test evidence, SRS traceability | Not a code module; no imports | Not applicable |

## Dependency direction rule

Dependencies flow inward toward `shared/`. No circular dependencies are permitted.

```
host/backend/  --imports-->  shared/constants/
host/frontend/ --consumes via WebSocket JSON only-->  (no module imports)
firmware/      --mirrors via C++ headers-->           shared/schemas/  (no Python import)
shared/        --no imports-->  (stands alone)
```

The frontend and firmware never import Python modules from each other or from the backend. Their only coupling to the backend is through the wire protocol defined in `shared/schemas/` and documented in `docs/architecture/websocket-protocol.md`.

## Why these rules exist

**NFR-016** requires that host backend, host frontend, firmware, shared protocol, and documentation concerns are separated in the codebase. Mixing modules would make it impossible to reason about which subsystem owns a given piece of state.

**NFR-018** requires that new games be addable without modifying core infrastructure beyond defined integration points. If game code could reach into frontend modules or firmware directly, adding a game would require changes across all three subsystems.

**NFR-019** requires that protocol messages and key domain models be documented. The `shared/` directory is the enforcement point: all message types must have a JSON Schema definition there before any implementation depends on them.

## Backend internal structure (planned)

Within `host/backend/`, the following internal ownership boundaries apply:

| Sub-package | Owns |
| --- | --- |
| `host/backend/api/` | FastAPI routers, WebSocket endpoint handlers, HTTP request/response models |
| `host/backend/core/` | Session manager, device registry, connection manager, heartbeat monitor, scoring service |
| `host/backend/games/` | Game module loader, game interface definition, all built-in game implementations |
| `host/backend/db/` | SQLite schema, repository pattern implementations, migration helpers |

Game implementations in `host/backend/games/` may import from `host/backend/core/` through the game interface only. They must not bypass the interface to write state directly to the database or push WebSocket messages directly.

## Firmware internal structure (planned)

Within `firmware/src/`, board-specific configuration must be isolated per SRS NFR-017 and FW-001, FW-002, FW-006:

| Sub-directory | Owns |
| --- | --- |
| `firmware/src/protocol/` | C++ header files mirroring `shared/schemas/` field names and `shared/constants/protocol.py` values |
| `firmware/src/config/` | Board-specific pin mappings and feature switches (`board_config.h`) |
| `firmware/src/app/` | Common application logic independent of board target |

Changing the target board (e.g. from ESP32-C3 to ESP32-S3) must require changes only in `firmware/src/config/`, not in application or protocol source files. This directly satisfies SRS AC-015.

## Enforcing the rules

At present, the rules are enforced by convention and code review. Future CI additions may include:

- Import linter checks preventing backend from importing frontend modules.
- Dependency graph verification as part of the test suite.
- Schema validation CI step confirming all wire messages match their JSON Schema definitions.

All violations discovered during development must be resolved before merging, not deferred. If a legitimate cross-boundary need is identified, the boundary rule must be formally revised in this document and the SRS traceability updated accordingly.
