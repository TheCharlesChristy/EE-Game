# Contributing to EE-Game

## Project structure

```
host/backend/     Python 3.12 backend — FastAPI, SQLite, game engine
host/frontend/    React 18 + TypeScript — host control and public display
firmware/         PlatformIO + Arduino — ESP32-C3 firmware
shared/           Versioned JSON schemas and protocol constants
docs/             SRS, epic specifications, deployment runbooks
scripts/          CI helpers and the Python device simulator
```

---

## Environment setup

**Prerequisites:** Python 3.12+, Node.js 18+, Git. PlatformIO only needed for firmware.

```bash
git clone https://github.com/your-org/ee-game.git
cd ee-game

# Backend
cd host/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd host/frontend
npm install
```

---

## Running in development

Open two terminals from the repository root:

```bash
# Terminal 1 — backend (auto-reloads on file changes)
cd host/backend && source .venv/bin/activate
uvicorn ee_game_backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — frontend dev server (proxies API/WebSocket to backend)
cd host/frontend && npm run dev
```

| URL | Purpose |
|-----|---------|
| `http://localhost:5173/host` | Host control panel |
| `http://localhost:5173/display` | Public leaderboard display |
| `http://localhost:8000/health` | Backend health |
| `http://localhost:8000/docs` | Auto-generated API reference |

**Simulating devices (no ESP32 hardware needed):**

```bash
cd scripts/tools
python device_simulator.py --devices 5 --host localhost --port 8000
```

This registers five virtual players and sends heartbeats and game events, letting you run a full session in the browser without physical hardware.

---

## Testing

Always run tests before opening a pull request.

**Backend:**

```bash
cd host/backend && source .venv/bin/activate
pytest                    # all tests
pytest tests/test_round_service.py   # single file
pytest -k "scoring"       # filter by name
```

**Frontend:**

```bash
cd host/frontend
npm test                  # all tests (vitest)
npm run build             # confirm production build is clean
```

**Lint:**

```bash
cd host/backend && ruff check .     # Python
cd host/frontend && npm run lint    # TypeScript/TSX
```

---

## Adding a new game

Games are Python classes implementing the `Game` contract in
`host/backend/ee_game_backend/games/contract.py`. Each game lives in its own
sub-package under `host/backend/ee_game_backend/games/<game_id>/`.

**Minimum required files:**

```
games/<game_id>/
    __init__.py       # empty
    metadata.py       # GameMetadata instance (title, category, instructions, etc.)
    logic.py          # GameImpl(Game) — the game class itself
```

**Implement the contract:**

```python
# logic.py
from ee_game_backend.games.contract import Game, GameMetadata, RoundResult, TestResult

class GameImpl(Game):
    @property
    def metadata(self) -> GameMetadata:
        from .metadata import METADATA
        return METADATA

    def setup_content(self) -> dict:
        # Return parts list, build instructions, diagram path, etc.
        ...

    def validate_test_event(self, device_id: str, payload: dict) -> TestResult:
        # Return TestResult.PASS, FAIL, or NOT_TESTED
        ...

    def handle_live_event(self, device_id: str, payload: dict, state: dict) -> dict:
        # Process an in-round event; return updated round state
        ...

    def score_round(self, state: dict, players: list[str]) -> dict[str, int]:
        # Return {device_id: points} for each player
        ...

    def format_result(self, state: dict, scores: dict[str, int]) -> dict:
        # Return display payload for the results screen
        ...
```

**Register the game** by adding its module path to `BUILTIN_GAME_MODULES` in
`host/backend/ee_game_backend/games/registry.py`.

**Write tests** in `host/backend/tests/` — at minimum, cover `score_round` with
a normal case, a tie, and an all-fail case.

**Add a game spec** in `docs/games/<game_id>.md` — title, player count,
hardware needed, scoring rules, and any edge cases.

---

## Backend architecture

The backend follows a layered pattern with strict module boundaries:

| Layer | Modules | Responsibility |
|-------|---------|----------------|
| API | `api/` | FastAPI routes, WebSocket endpoints |
| Services | `session/`, `round/`, `scoring/`, `registry/` | Business logic, state machines |
| Games | `games/` | Game contract, registry, built-in implementations |
| Core | `core/` | Connection manager, message router, heartbeat |
| Persistence | `session/repository.py`, `session/database.py` | SQLite via aiosqlite |

**Key conventions:**

- Services communicate with each other by direct reference (injected via `app.state`), not by importing each other's modules.
- State is broadcast to the frontend over WebSocket after every mutation — use the `_broadcast` helper pattern in `SessionService`.
- All state transitions must write an `AuditEvent`. Use `AuditEvent.new(action_type=..., ...)` from `session/models.py`.
- The database uses a migration runner (`session/migrations.py`). Add new tables there — never alter existing column definitions in a migration, only add.
- `datetime.datetime.now(datetime.UTC)` throughout — `utcnow()` is deprecated.

---

## Frontend architecture

The frontend is a single React app that renders in two modes determined by the URL:

- `/host/*` — host control panel (session management, game selection, live controls)
- `/display/*` — public display (driven entirely by WebSocket state, no user interaction)

**State management:** A single Zustand store in `src/state/store.ts` holds the
authoritative frontend state, populated by WebSocket messages from the backend.
Components read from the store and do not fetch REST endpoints for live data.

**REST client:** `src/api/client.ts` wraps the backend REST API for mutations
(creating sessions, triggering transitions, manual score adjustments). It is not
used for reading live state — that comes from the WebSocket.

**Adding a new screen:** Create a route component under
`src/routes/host/` or `src/routes/display/`, add it to the router in
`HostControl.tsx` or `PublicDisplay.tsx`, and consume state from the store.

---

## Protocol

All WebSocket messages follow the envelope defined in `shared/`:

```json
{
    "version": "1",
    "type": "<message_type>",
    "device_id": "<sender>",
    "payload": {}
}
```

Message type constants are in `shared/constants/protocol.py` (backend) and
mirrored in `firmware/src/protocol/message_types.h` (firmware).

JSON schemas for each message type are in `shared/schemas/v1/`. The backend
validates incoming messages against these schemas in `MessageRouter`.

**Adding a new message type:**

1. Add the constant to `shared/constants/protocol.py` and `message_types.h`.
2. Add a JSON schema to `shared/schemas/v1/<type>.schema.json`.
3. Add a dispatch case to `core/message_router.py`.
4. Handle it in firmware `src/protocol/message_codec.cpp`.

---

## Pull request checklist

- [ ] `pytest` passes with no failures
- [ ] `ruff check .` is clean
- [ ] `npm test` passes
- [ ] `npm run build` succeeds
- [ ] New game or API change has corresponding tests
- [ ] New message type has a schema in `shared/schemas/v1/`
- [ ] Database additions are behind a migration in `session/migrations.py`
