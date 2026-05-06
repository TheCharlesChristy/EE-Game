# EE-Game

An offline multiplayer game platform for hands-on electronics education. Up to 20 students each build circuits on a breadboard connected to an ESP32 device, compete in real-time engineering challenges, and see results on a shared display — all hosted locally on a Raspberry Pi with no internet required.

Built for classroom use, STEM clubs, and live events with students aged 14–18.

---

## How it works

```
┌─────────────┐      WiFi (local)      ┌──────────────────┐
│  Raspberry  │ ◄────────────────────► │  ESP32-C3        │
│  Pi (host)  │                        │  + breadboard    │
│             │ ◄────────────────────► │  (×20 players)   │
│  Backend    │      WebSocket         └──────────────────┘
│  + React UI │
│             │ ◄────── browser ───────  Host laptop
└─────────────┘ ◄────── browser ───────  Room display screen
```

The facilitator selects a game, students build the required circuit, and the backend scores events in real time. Results appear on a room-facing leaderboard. Sessions can be saved, paused, and resumed across restarts.

---

## Features

- **10 built-in games** — reaction timing, quiz buzzer, analog dial, pattern memory, circuit building, Morse decode, team tug-of-war, voltage estimation, sequence tap, resistor colour code
- **Live leaderboard** — WebSocket-driven public display, readable from across a room
- **Team rounds** — random team allocation per round for selected games
- **Host controls** — pause, repair, manual score adjustments with full audit trail
- **Session persistence** — save and resume across reboots; finished sessions are archived and anonymised
- **Fully offline** — Pi acts as its own WiFi access point; no internet needed at runtime

---

## Getting started

**Install on a Raspberry Pi:**

```bash
git clone https://github.com/your-org/ee-game.git
cd ee-game
./install-pi.sh
sudo systemctl start ee-game
```

For a standalone classroom setup with a built-in WiFi access point:

```bash
./install-pi.sh --configure-wifi-ap --wifi-ssid "EE-Game"
```

**Flash an ESP32 device:**

```bash
./flash-device.sh                        # auto-detect port, ESP32-C3 target
./flash-device.sh --port /dev/ttyUSB0   # specify port
```

See [setup.md](setup.md) for full hardware requirements and options.

---

## Documentation

| Document | Contents |
|----------|----------|
| [setup.md](setup.md) | Hardware list, installation, flashing |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development workflow, architecture, adding games |
| [docs/deployment/raspberry-pi-setup.md](docs/deployment/raspberry-pi-setup.md) | Full Pi deployment guide (offline install, WiFi AP, permissions) |
| [docs/deployment/service-management.md](docs/deployment/service-management.md) | Starting, stopping, updating, log viewing |
| [docs/deployment/recovery-runbook.md](docs/deployment/recovery-runbook.md) | Troubleshooting common failures |
| [docs/electronic_engineering_game_SRS_v1.md](docs/electronic_engineering_game_SRS_v1.md) | Full software requirements specification |

---

## Tech stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, FastAPI, SQLite, aiosqlite |
| Frontend | React 18, TypeScript, Vite |
| Firmware | C++, Arduino framework, PlatformIO |
| Protocol | JSON over WebSocket, versioned schemas |
| Host hardware | Raspberry Pi 4 / 5 |
| Player hardware | ESP32-C3 |

---

## Licence

[MIT](LICENSE)
