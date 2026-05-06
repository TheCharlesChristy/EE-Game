# Raspberry Pi Setup and Installation Guide

**SRS references:** Section 13.1 (Deployment), AC-011, NFR-007, NFR-024
**Epic:** EP-01 — Platform Foundation
**User story:** EP-01-US-03

This guide covers everything required to install and operate the EE-Game platform on a Raspberry Pi 4. All steps are designed to work offline once preparation is complete. No internet access is required at runtime (SRS Section 13.1, NFR-024).

---

## Prerequisites

### Hardware

- Raspberry Pi 4 Model B (2 GB RAM minimum; 4 GB or 8 GB recommended for comfortable headroom)
- 16 GB microSD card (8 GB minimum; class 10 or better)
- Official Raspberry Pi power supply (5V 3A USB-C)
- Ethernet cable or WiFi (used only during initial setup; not needed at runtime)

### Operating System

- Raspberry Pi OS Bookworm (64-bit) — the Lite image is sufficient; the Desktop image works too
- Debian 12 (Bookworm) or any compatible 64-bit Debian-based OS is also acceptable
- Python 3.12 or later must be available (`python3 --version` to verify)

### Accounts and Access

- SSH access to the Pi, or a keyboard and monitor for direct access
- A separate machine with internet access for the offline preparation steps below

---

## Offline Preparation (on a machine with internet access)

Complete these steps on a laptop or desktop that has internet access. The output is copied to a USB drive or SD card for transfer to the Pi.

### Step 1 — Clone or copy the repository

```bash
git clone https://github.com/your-org/ee-game.git
# Or unzip the release archive
```

### Step 2 — Download Python dependencies to a local wheel cache

The Pi will install Python packages from this cache without needing the internet.

```bash
cd ee-game/host/backend
pip wheel -w /tmp/ee-game-wheels ".[dev]"
```

This downloads all runtime and development dependencies declared in `pyproject.toml` (fastapi, uvicorn, pydantic-settings, pydantic, websockets, and dev extras) into `/tmp/ee-game-wheels/`.

Verify the cache is populated:

```bash
ls /tmp/ee-game-wheels/
```

You should see `.whl` files for each dependency.

### Step 3 — Build the React frontend

Node.js 18 or later and npm are required on the build machine.

```bash
cd ee-game/host/frontend
npm install
npm run build
```

This produces `host/frontend/dist/`. The backend serves this directory as static files, so it must be present at `/opt/ee-game/host/frontend/dist/` on the Pi.

The repository root also includes a release helper:

```bash
./scripts/build-release.sh
```

It runs the frontend build and compiles the backend package as a quick release sanity check.

### Step 4 — Bundle everything for transfer

Copy the repository, the wheel cache, and the built frontend to a USB drive:

```bash
cp -r ee-game /media/usb/ee-game
cp -r /tmp/ee-game-wheels /media/usb/ee-game-wheels
# dist/ is already inside ee-game/host/frontend/dist from step 3
```

---

## Pi Installation Steps

Perform the following on the Raspberry Pi with the USB drive attached.

### Step 1 — Create the service user

The application runs under a dedicated system account with no login shell, limiting the impact of any security issue.

```bash
sudo useradd --system --shell /bin/false --home /opt/ee-game ee-game
sudo mkdir -p /opt/ee-game
```

### Step 2 — Copy the repository to `/opt/ee-game`

```bash
sudo cp -r /media/usb/ee-game/. /opt/ee-game/
sudo chown -R ee-game:ee-game /opt/ee-game
```

Verify the structure looks correct:

```bash
ls /opt/ee-game/
# Expected: host/  firmware/  shared/  docs/  (and other repo files)

ls /opt/ee-game/host/frontend/dist/
# Expected: index.html and bundled assets from the React build
```

### Step 3 — Create the Python virtual environment and install from local wheels

```bash
cd /opt/ee-game/host/backend
sudo -u ee-game python3 -m venv .venv
sudo -u ee-game .venv/bin/pip install --no-index --find-links=/media/usb/ee-game-wheels -e .
```

The `--no-index` flag tells pip not to contact PyPI. The `--find-links` flag points to the local wheel cache. The `-e .` installs the `ee-game-backend` package in editable mode from the current directory.

Verify the installation:

```bash
sudo -u ee-game /opt/ee-game/host/backend/.venv/bin/python -c "import ee_game_backend; print('OK')"
```

### Step 4 — Set up the environment file

```bash
sudo -u ee-game cp /opt/ee-game/docs/deployment/.env.production.example /opt/ee-game/host/backend/.env
sudo chmod 600 /opt/ee-game/host/backend/.env
sudo -u ee-game nano /opt/ee-game/host/backend/.env
```

Review the values in `.env`. For most deployments the defaults are correct. See `.env.production.example` for a description of each variable.

### Step 5 — Install the systemd service

```bash
sudo cp /opt/ee-game/docs/deployment/ee-game.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ee-game
```

`enable` configures the service to start automatically when the Pi boots.

### Step 6 — Start the service and verify it is running

```bash
sudo systemctl start ee-game
sudo systemctl status ee-game
```

The status output should show `Active: active (running)`. If it shows `failed`, see the Recovery Runbook.

### Step 7 — Verify the health endpoint responds

```bash
curl http://localhost:8000/health
```

A healthy response looks like:

```json
{"status": "ok"}
```

If this returns a connection error, the service is not listening. Check the logs:

```bash
sudo journalctl -u ee-game -n 50 --no-pager
```

---

## Networking — Access Point Setup

For standalone operation at a venue, the Raspberry Pi is configured as a WiFi access point. ESP32 devices and operator browsers connect to the Pi directly; no external router or internet connection is needed (SRS Section 13.1, NFR-024).

**Required packages** (install offline from pre-downloaded `.deb` files):

- `hostapd` — manages the WiFi access point
- `dnsmasq` — provides DHCP addresses to connecting devices

To download these packages for offline installation on a machine with internet:

```bash
apt-get download hostapd dnsmasq
# Copy the resulting .deb files to the Pi via USB drive
```

On the Pi, install from the `.deb` files:

```bash
sudo dpkg -i /media/usb/hostapd_*.deb /media/usb/dnsmasq_*.deb
sudo apt-get install -f  # Fix any missing dependencies (requires internet or pre-downloaded deps)
```

**High-level configuration steps:**

Template configs are tracked in `scripts/wifi-ap/hostapd.conf` and
`scripts/wifi-ap/dnsmasq.conf`. Copy them to the matching `/etc/` locations and
change the WPA passphrase before classroom use.

1. Set a static IP on the `wlan0` interface — add to `/etc/dhcpcd.conf`:

   ```
   interface wlan0
   static ip_address=192.168.4.1/24
   nohook wpa_supplicant
   ```

2. Configure `/etc/hostapd/hostapd.conf`:

   ```
   interface=wlan0
   driver=nl80211
   ssid=ee-game
   hw_mode=g
   channel=7
   wmm_enabled=0
   macaddr_acl=0
   auth_algs=1
   ignore_broadcast_ssid=0
   wpa=2
   wpa_passphrase=<strong-password-here>
   wpa_key_mgmt=WPA-PSK
   rsn_pairwise=CCMP
   ```

   Replace `<strong-password-here>` with a memorable but non-trivial password. This is the password operators and devices need to connect.

3. Point `hostapd` at the config file — add to `/etc/default/hostapd`:

   ```
   DAEMON_CONF="/etc/hostapd/hostapd.conf"
   ```

4. Configure `/etc/dnsmasq.conf` to assign addresses in the `192.168.4.x` range:

   ```
   interface=wlan0
   dhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,24h
   ```

5. Enable and start the access point services:

   ```bash
   sudo systemctl unmask hostapd
   sudo systemctl enable hostapd dnsmasq
   sudo systemctl start hostapd dnsmasq
   ```

6. Reboot and verify the `ee-game` SSID is visible from a phone or laptop.

**Note:** The exact `hostapd` configuration (particularly `hw_mode` and `channel`) depends on the Pi's WiFi chip and regional regulations. Test the access point configuration in advance of the event.

---

## File Permissions Summary

| Path | Owner | Permissions | Reason |
|------|-------|-------------|--------|
| `/opt/ee-game/` | ee-game:ee-game | 755 | Application root; readable by all, writable only by service user |
| `/opt/ee-game/host/backend/.env` | ee-game:ee-game | 600 | Contains configuration values; not world-readable |
| `/opt/ee-game/host/backend/.venv/` | ee-game:ee-game | 755 | Python virtual environment |
| `/opt/ee-game/host/frontend/dist/` | ee-game:ee-game | 755 | Built React assets served as static files |
| `/etc/systemd/system/ee-game.service` | root:root | 644 | systemd unit file; managed by root |

To verify permissions are correct:

```bash
stat /opt/ee-game/host/backend/.env
# Should show: Access: (0600/-rw-------)  Uid: (ee-game)
```

---

## Updating the Software

Follow this procedure to update to a new version without losing session data (NFR-007, NFR-008).

1. Stop the service:

   ```bash
   sudo systemctl stop ee-game
   ```

2. Back up the environment file and any SQLite database files:

   ```bash
   cp /opt/ee-game/host/backend/.env ~/ee-game.env.bak
   # If a data directory exists:
   cp -r /opt/ee-game/host/backend/data/ ~/ee-game-data-bak/
   ```

3. Copy the new application files:

   ```bash
   sudo rsync -av --exclude='.env' --exclude='data/' /media/usb/ee-game/. /opt/ee-game/
   sudo chown -R ee-game:ee-game /opt/ee-game
   ```

4. If Python dependencies changed, reinstall from the new wheel cache:

   ```bash
   sudo -u ee-game /opt/ee-game/host/backend/.venv/bin/pip install \
     --no-index --find-links=/media/usb/ee-game-wheels -e /opt/ee-game/host/backend/
   ```

5. Restore the environment file if it was overwritten:

   ```bash
   sudo -u ee-game cp ~/ee-game.env.bak /opt/ee-game/host/backend/.env
   sudo chmod 600 /opt/ee-game/host/backend/.env
   ```

6. If the frontend changed, copy the new `dist/`:

   ```bash
   sudo cp -r /media/usb/ee-game/host/frontend/dist /opt/ee-game/host/frontend/
   sudo chown -R ee-game:ee-game /opt/ee-game/host/frontend/dist
   ```

7. Reload systemd if the service unit changed:

   ```bash
   sudo systemctl daemon-reload
   ```

8. Start the service and verify it is healthy:

   ```bash
   sudo systemctl start ee-game
curl http://localhost:8000/health
```

For a broader deployment check, run:

```bash
EE_GAME_URL=http://localhost:8000 ./scripts/smoke-test.sh
```
