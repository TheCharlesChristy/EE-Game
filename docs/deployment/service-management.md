# Service Management — Operator Guide

**SRS references:** Section 13.1 (Deployment), Section 13.2 (Logging and Diagnostics), OP-001–OP-005, NFR-007, NFR-010
**Epic:** EP-01 — Platform Foundation
**User story:** EP-01-US-03

This guide covers the day-to-day operations that operators need to manage the EE-Game application on the Raspberry Pi. No programming knowledge is required. All commands are run in a terminal on the Pi (either via SSH or with a keyboard and monitor attached).

---

## 1. Starting the Application

```bash
sudo systemctl start ee-game
```

Wait a few seconds, then confirm it is running:

```bash
sudo systemctl status ee-game
```

You should see `Active: active (running)`. The application is now ready to accept connections.

The `ee-game` service is also configured to start automatically whenever the Pi boots, so you normally do not need to start it manually after a power cycle.

---

## 2. Stopping the Application

```bash
sudo systemctl stop ee-game
```

This stops the application cleanly. Any active session will be left in its last saved state and can be resumed the next time the service starts (NFR-007).

---

## 3. Restarting the Application

```bash
sudo systemctl restart ee-game
```

Use this after changing the `.env` configuration file, after updating the software, or when the service is misbehaving but has not crashed outright. A restart stops the application and starts it again immediately.

---

## 4. Checking Service Status

```bash
sudo systemctl status ee-game
```

**What the output means:**

| Status shown | Meaning | Action |
|---|---|---|
| `Active: active (running)` | The application is running normally. | None required. |
| `Active: activating (start)` | The application is starting up. | Wait 5–10 seconds and check again. |
| `Active: inactive (dead)` | The application has been stopped deliberately. | Run `sudo systemctl start ee-game` if it should be running. |
| `Active: failed` | The application crashed or failed to start. | See the recovery runbook. Check logs with `sudo journalctl -u ee-game -n 50 --no-pager`. |
| `Active: activating (auto-restart)` | The application crashed and systemd is about to restart it. | Wait 10 seconds; if it keeps cycling, consult the recovery runbook. |

---

## 5. Viewing Logs

### Last 100 log lines (good for a quick check):

```bash
sudo journalctl -u ee-game -n 100 --no-pager
```

### Live log tail (shows new entries as they appear — press Ctrl+C to stop):

```bash
sudo journalctl -u ee-game -f
```

### Logs from the current boot only:

```bash
sudo journalctl -u ee-game -b --no-pager
```

### Logs filtered to errors and above:

```bash
sudo journalctl -u ee-game -p err --no-pager
```

Log entries are timestamped. Look for lines containing `ERROR` or `CRITICAL` if something has gone wrong. Normal startup produces INFO-level lines confirming the server is listening on port 8000. Session lifecycle events (create, save, pause, resume, finish) are logged at INFO level (OP-001).

---

## 6. Testing the Health Endpoint

Run this from the Pi to confirm the backend is responding:

```bash
curl http://localhost:8000/health
```

A healthy response looks like:

```json
{"status": "ok"}
```

If you get `curl: (7) Failed to connect` the service is not running or is not listening on port 8000. Check the service status and logs.

To test from another device on the same network (for example, the operator's laptop connected to the `ee-game` WiFi):

```bash
curl http://192.168.4.1:8000/health
```

Replace `192.168.4.1` with the Pi's IP address if it is configured differently.

---

## 7. Checking the Web Interface

Open a browser on any device connected to the `ee-game` WiFi network and navigate to:

- **Public display** (room-facing leaderboard): `http://192.168.4.1:8000/display`
- **Host control panel** (operator dashboard): `http://192.168.4.1:8000/host`

Both pages should load without a white screen or error message. If the page fails to load:

1. Confirm the service is running: `sudo systemctl status ee-game`
2. Confirm the frontend files were built and copied: `ls /opt/ee-game/host/frontend/dist/`
3. Check for asset errors in the browser's developer console (F12 in most browsers)

---

## 8. Verifying Device Connections

When an ESP32 device boots and connects to the `ee-game` WiFi, it registers with the backend over WebSocket. Successful device connections appear in the logs as lines containing `[WebSocket] Device connected` along with the device identifier (OP-002).

To watch for device connections live:

```bash
sudo journalctl -u ee-game -f
```

Power on a device and wait 10–15 seconds. You should see a connection event appear in the log. The device should also appear in the host control panel at `http://192.168.4.1:8000/host`.

Device heartbeat events are logged at DEBUG level and confirm liveness after the initial connection (OP-002). If a device goes stale (heartbeat timeout of 30 seconds by default), a disconnect event is logged at INFO level.

---

## 9. Automatic Restart on Crash

The `ee-game` service is configured with `Restart=on-failure` and `RestartSec=5s`. This means systemd will automatically restart the application 5 seconds after an unexpected crash, without any operator action (NFR-010).

If the application crashes three or more times in quick succession, systemd enters a backoff state and stops restarting automatically. The status will show `failed`. To manually reset and restart:

```bash
sudo systemctl reset-failed ee-game
sudo systemctl start ee-game
```

If the application continues to crash immediately after this, do not keep restarting it. Note the error from the logs (`sudo journalctl -u ee-game -n 200 --no-pager`) and consult the Recovery Runbook.
