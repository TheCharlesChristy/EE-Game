# EE-Game - Setup Guide

## Hardware required

**Host (game server)**
- Raspberry Pi 4 or 5, 2 GB RAM minimum (4 GB+ recommended)
- 16 GB microSD card, Class 10 or better
- Official USB-C power supply (5 V / 3 A)
- Second screen + HDMI cable for the public leaderboard display

**Player devices** (one per player, up to 20)
- ESP32-C3 development board
- Breadboard + component kit (parts list shown on-screen per game)
- USB cable for initial flashing

---

## Installing on a Raspberry Pi

```bash
# 1. Clone the repo (once)
git clone https://github.com/TheCharlesChristy/EE-Game.git
cd EE-Game

# 2. Edit .env — set your WiFi name, password, and backend port
vi .env

# 3. Install system dependencies (once, on a fresh Pi)
sudo ./install-deps.sh

# 4. Install and start the app
sudo ./install-pi.sh
```

That's it. The service starts automatically and survives reboots.

**To update after a git pull:**
```bash
git pull
ee-game restart       # or: ee-game update (rebuilds frontend + deps too)
```

---

## Managing the service

```bash
ee-game status        # health check, connected devices, config
ee-game logs -f       # live logs
ee-game restart       # restart after config changes
ee-game stop
ee-game start
```

**Edit config:**
```bash
ee-game config                          # show current config (password masked)
ee-game config set WIFI_PASSWORD newpw  # change a value
ee-game restart                         # apply changes
```

---

## Flashing ESP32 devices

WiFi credentials are read from `.env` and baked into the firmware automatically.

**On the Pi (after install):**
```bash
ee-game flash                           # auto-detect port, esp32-c3 target
ee-game flash --port /dev/ttyUSB0      # specify port
ee-game flash --target esp32dev        # different board variant
ee-game flash --monitor                # open serial console after flash
```

**From a laptop (before or without a Pi):**
```bash
./flash-device.sh                       # reads credentials from .env
./flash-device.sh --port /dev/ttyUSB0
./flash-device.sh --target esp32dev --monitor
```

Both scripts always do a clean build before flashing, so changing the WiFi SSID
or password in `.env` is always picked up.

---

## Local development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development workflow.

Quick start:

```bash
# Backend
cd host/backend && python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn ee_game_backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd host/frontend && npm install && npm run dev
```

| URL | Page |
|-----|------|
| `http://localhost:5173/` | Landing (pick host or display) |
| `http://localhost:5173/host` | Host control panel |
| `http://localhost:5173/display` | Public display |
| `http://localhost:8000/health` | Backend health check |
