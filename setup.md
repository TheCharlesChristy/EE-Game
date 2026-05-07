# EE-Game — Setup Guide

## What you need

**Game server (runs once, stays at the venue)**
- Raspberry Pi 4 or 5, 2 GB RAM minimum
- 16 GB microSD card (Class 10 or faster)
- Official USB-C power supply (5 V / 3 A)
- A screen + HDMI cable for the public leaderboard display
- Internet connection for the initial install (Ethernet recommended)

**Player devices** (one per player, up to 20)
- ESP32-C3 development board
- Breadboard + component kit (the game tells you which parts per round)
- USB cable for initial flashing

---

## Installing on a Raspberry Pi

### Step 1 — Fill in your WiFi details

Open the `.env` file in the repository root and set the name and password
for the game WiFi network the Pi will create:

```
WIFI_SSID=YourGameName
WIFI_PASSWORD=YourPassword
```

The password must be at least 8 characters.

### Step 2 — Run the installer

Connect the Pi to the internet (Ethernet is simplest), then run:

```bash
sudo ./install.sh
```

That's it. The script handles everything — packages, backend, frontend,
and WiFi configuration. It takes about 5 minutes.

> **Note:** Your current network connection is not affected during the
> install. The game WiFi only starts after you reboot.

### Step 3 — Reboot

```bash
sudo reboot
```

After the reboot, the Pi broadcasts the game WiFi and the backend starts
automatically. Connect any device to the game WiFi and open the host panel:

```
http://192.168.4.1:8000/host
```

---

## Managing the service

```bash
ee-game status        # is everything running?
ee-game logs -f       # live log output
ee-game restart       # restart after a config change
ee-game stop
ee-game start
```

**Change a config value:**
```bash
ee-game config set WIFI_PASSWORD newpassword
sudo reboot           # WiFi password changes need a reboot
```

---

## Flashing ESP32 devices

WiFi credentials are read from `.env` and baked into the firmware automatically.

**From the Pi (after install):**
```bash
ee-game flash                           # auto-detect port, esp32-c3 target
ee-game flash --port /dev/ttyUSB0      # specify port
ee-game flash --monitor                # open serial console after flash
```

**From a laptop (before or without a Pi):**
```bash
./flash-device.sh
./flash-device.sh --port /dev/ttyUSB0
./flash-device.sh --target esp32dev --monitor
```

Both always do a clean build, so changing WiFi credentials in `.env`
is always picked up.

---

## Updating after a code change

```bash
git pull
ee-game update        # rebuilds frontend + backend, restarts service
```

---

## Local development

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

Developer tools (PlatformIO for ESP32 flashing):
```bash
sudo ./install-deps.sh
```
