# EE-Game - Setup Guide

A local-network multiplayer game platform for electronics education. The backend runs on a Raspberry Pi; ESP32 devices connect over WiFi; players and the host use a browser.

---

## Prerequisites

### Hardware

**Host machine (game server):**
- Raspberry Pi 4 Model B or 5 - 2 GB RAM minimum, 4 GB or 8 GB recommended
- 16 GB microSD card, Class 10 or better (8 GB minimum)
- Official Raspberry Pi USB-C power supply (5 V / 3 A)
- A second screen and HDMI cable for the public display (room-facing leaderboard)

**Player devices (one per player, up to 20):**
- ESP32-C3 development board (other ESP32-family variants also supported)
- Half-size or full-size breadboard
- Component kit per game (resistors, LEDs, wire jumpers, potentiometers - exact list varies by game and is shown on-screen during the build phase)
- USB cable for initial firmware flashing; battery pack or USB power for standalone play

**Networking:**
- No external router or internet connection needed at runtime - the Pi acts as its own WiFi access point
- A laptop or tablet for the host control panel (connects to the Pi's WiFi)

---

### Software

| Tool | Minimum version | Check |
|------|----------------|-------|
| Python | 3.12 | `python3 --version` |
| pip | 23+ | `pip --version` |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |
| PlatformIO CLI | 6 | `pio --version` (firmware only) |
| Git | any | `git --version` |

PlatformIO is only needed if you are flashing firmware onto ESP32 devices. Everything else runs without it.

---

## 1. Clone the repository

```bash
git clone https://github.com/your-org/ee-game.git
cd ee-game
```

---

## 2. Backend setup

```bash
cd host/backend

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install the package and all dependencies
pip install -e ".[dev]"
```

Verify the installation:

```bash
python -c "import ee_game_backend; print('OK')"
```

---

## 3. Frontend setup

```bash
cd host/frontend
npm install
```

---

## 4. Running locally (development)

Open two terminals.

**Terminal 1 - backend:**

```bash
cd host/backend
source .venv/bin/activate
uvicorn ee_game_backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - frontend dev server:**

```bash
cd host/frontend
npm run dev
```

Then open:

| URL | What you see |
|-----|-------------|
| `http://localhost:5173/host` | Host control panel (session, games, live round) |
| `http://localhost:5173/display` | Public display (room-facing leaderboard) |
| `http://localhost:8000/health` | Backend health check (should return `{"status":"ok"}`) |

The frontend dev server proxies API and WebSocket requests to the backend automatically.

---

## 5. Running tests

**Backend:**

```bash
cd host/backend
source .venv/bin/activate
pytest
```

**Frontend:**

```bash
cd host/frontend
npm test
```

**Lint (backend):**

```bash
cd host/backend
ruff check .
```

**All at once via Make:**

```bash
make backend-test
make frontend-test
```

---

## 6. Building for production

The production build compiles the React frontend into static files that the backend serves directly (no separate Node.js process needed at runtime).

```bash
# Build frontend assets
make frontend-build
# Output: host/frontend/dist/

# Verify the full build (frontend + backend compile check)
make release
```

After building, start the backend alone and it serves the UI at `http://localhost:8000`:

```bash
cd host/backend
source .venv/bin/activate
uvicorn ee_game_backend.main:app --host 0.0.0.0 --port 8000
```

---

## 7. Firmware (ESP32 devices)

Flashing is only needed when setting up physical devices. You can develop and test the backend/frontend without any hardware using the Python device simulator.

**Flash real devices:**

```bash
cd firmware

# Build for ESP32-C3 (default target)
pio run -e esp32-c3

# Build and flash to a connected device
pio run -e esp32-c3 --target upload

# Monitor serial output
pio device monitor
```

Supported environments defined in `firmware/platformio.ini`: `esp32-c3`, `esp32dev`.

**Simulate devices (no hardware needed):**

```bash
cd scripts/tools
python device_simulator.py --devices 5 --host localhost --port 8000
```

This starts five virtual devices that register, send heartbeats, and emit game events - enough to run a full session in the browser without physical hardware.

---

## 8. Deploying to Raspberry Pi

For a classroom or event deployment, the Pi acts as both the WiFi access point and the game server. The full procedure is documented in [docs/deployment/raspberry-pi-setup.md](docs/deployment/raspberry-pi-setup.md) and covers:

- Creating the `ee-game` system user
- Installing from an offline wheel cache (no internet needed on the Pi)
- Setting up the `systemd` service for auto-start on boot
- Configuring `hostapd` + `dnsmasq` to create the WiFi access point

**Quick path (if the Pi already has internet access during setup):**

```bash
# On the Pi, from the cloned repository
cd host/frontend && npm install && npm run build && cd ../..
./scripts/install-pi.sh
sudo systemctl start ee-game
curl http://localhost:8000/health
```

`install-pi.sh` copies the application to `/opt/ee-game/`, installs the systemd unit, and enables it to start on boot.

After deployment, operators connect their browser to `http://192.168.4.1:8000/host` (or whatever IP is assigned to the Pi's `wlan0` interface) and ESP32 devices connect to the same WiFi network automatically.

---

## 9. Project structure (quick reference)

```
host/backend/     Python 3.12 backend - FastAPI, SQLite, game engine
host/frontend/    React 18 + TypeScript - host control and public display
firmware/         PlatformIO + Arduino - ESP32-C3 device firmware
shared/           Versioned JSON schemas and protocol constants
docs/             SRS, epic specs, deployment runbooks
scripts/          Build, install, smoke-test, device simulator
```

For more detail on the deployment, recovery, and service management, see `docs/deployment/`.
