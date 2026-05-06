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

Clone the repository onto the Pi, then install system dependencies first:

```bash
sudo ./install-deps.sh
```

For a classroom deployment that also needs a WiFi access point and firmware flashing:

```bash
sudo ./install-deps.sh --with-wifi-ap --with-platformio
```

Then install the application:

```bash
./install-pi.sh
```

For a full production classroom setup in one command:

```bash
./install-pi.sh --prod --wifi-ssid "EE-Game" --wifi-password "yourpassphrase"
```

Start the service and verify it is healthy:

```bash
sudo systemctl start ee-game
curl http://localhost:8000/health
```

Run `./install-pi.sh --help` for all options (custom install path, port, dry-run, etc.).

Full details - offline installation, file permissions, updating - are in
[docs/deployment/raspberry-pi-setup.md](docs/deployment/raspberry-pi-setup.md).

---

## Flashing ESP32 devices

With a device connected via USB:

```bash
./flash-device.sh
```

Common options:

```bash
./flash-device.sh --port /dev/ttyUSB0          # specify port explicitly
./flash-device.sh --target esp32dev            # different board variant
./flash-device.sh --monitor                    # open serial console after flash
./flash-device.sh --build-only                 # compile without flashing
```

Run `./flash-device.sh --help` for all options.

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
| `http://localhost:5173/host` | Host control panel |
| `http://localhost:5173/display` | Public display |
| `http://localhost:8000/health` | Backend health check |
