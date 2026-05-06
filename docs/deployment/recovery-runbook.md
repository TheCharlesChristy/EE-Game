# Recovery Runbook

**SRS references:** Section 13.3 (Recovery Expectations), NFR-007, NFR-009, NFR-010, OP-001–OP-005
**Epic:** EP-01 — Platform Foundation
**User story:** EP-01-US-03

This runbook covers the most common failure scenarios for the EE-Game platform and provides step-by-step resolution procedures. Each scenario is structured as: **Symptom → Diagnosis → Resolution**.

For routine service operations (start, stop, restart, log viewing) see `service-management.md`.

---

## Scenario 1 — Service Fails to Start After Power Cycle

**Symptom**

`sudo systemctl status ee-game` shows:

```
Active: failed (Result: exit-code)
```

or the service appears inactive when it should be running after a reboot.

**Diagnosis**

Retrieve the most recent log entries:

```bash
sudo journalctl -u ee-game -n 50 --no-pager
```

Common causes and how to identify them in the logs:

| Log message or signal | Cause |
|---|---|
| `[Errno 2] No such file or directory: '/opt/ee-game/host/backend/.env'` | The `.env` file is missing |
| `PermissionError` or `Permission denied` | File ownership or permissions are wrong |
| `OSError: [Errno 98] Address already in use` | Port 8000 is already occupied by another process |
| Python `ImportError` or `ModuleNotFoundError` | The virtual environment is missing or packages were not installed |

**Resolution**

1. Fix the identified cause:

   - **Missing `.env`:** Copy the template and fill in values:
     ```bash
     sudo -u ee-game cp /opt/ee-game/docs/deployment/.env.production.example /opt/ee-game/host/backend/.env
     sudo chmod 600 /opt/ee-game/host/backend/.env
     ```

   - **Wrong permissions:** Restore correct ownership:
     ```bash
     sudo chown -R ee-game:ee-game /opt/ee-game
     sudo chmod 600 /opt/ee-game/host/backend/.env
     ```

   - **Port already in use:** Identify the occupying process and stop it:
     ```bash
     sudo ss -tlnp | grep 8000
     # Note the PID, then:
     sudo kill <PID>
     ```

   - **Missing packages:** Reinstall from the wheel cache:
     ```bash
     sudo -u ee-game /opt/ee-game/host/backend/.venv/bin/pip install \
       --no-index --find-links=/path/to/wheel-cache -e /opt/ee-game/host/backend/
     ```

2. Reset the failed state and start the service:

   ```bash
   sudo systemctl reset-failed ee-game
   sudo systemctl start ee-game
   sudo systemctl status ee-game
   ```

---

## Scenario 2 — Backend Is Running but No Web UI Loads

**Symptom**

The `ee-game` service is active and the health endpoint responds, but opening `http://<pi-ip>:8000/host` or `http://<pi-ip>:8000/display` in a browser shows a blank page, a `404 Not Found` error, or fails to connect.

**Diagnosis**

First, confirm the backend itself is healthy:

```bash
curl http://localhost:8000/health
```

If this returns `{"status": "ok"}`, the backend is running. The problem is likely the frontend assets.

Check whether the built frontend exists:

```bash
ls /opt/ee-game/host/frontend/dist/
```

If the directory is empty or does not exist, the React app was never built or copied. The backend cannot serve assets that are not there.

If the `dist/` directory exists, open the browser developer console (F12) on the failing page and look for asset loading errors (for example, `404` responses for `.js` or `.css` files).

**Resolution**

- **`dist/` directory missing or empty:** The frontend must be built on a machine with Node.js and npm, then copied to the Pi:

  On the build machine:
  ```bash
  cd ee-game/host/frontend
  npm install
  npm run build
  # Copy dist/ to a USB drive
  ```

  On the Pi:
  ```bash
  sudo cp -r /media/usb/dist /opt/ee-game/host/frontend/
  sudo chown -R ee-game:ee-game /opt/ee-game/host/frontend/dist
  sudo systemctl restart ee-game
  ```

- **Assets exist but browser shows errors:** The `STATIC_FILES_DIR` value in `.env` may be pointing to the wrong path. Verify:

  ```bash
  cat /opt/ee-game/host/backend/.env | grep STATIC_FILES_DIR
  ```

  The value should be `../frontend/dist` (relative to `host/backend/`). Correct it if needed and restart the service.

---

## Scenario 3 — ESP32 Devices Not Appearing in the Host Interface

**Symptom**

The backend is running and the browser-based host control panel loads, but no player devices appear after the ESP32 boards are powered on. The device count stays at zero.

**Diagnosis**

Work through the following checks in order:

1. Confirm the WiFi access point is running:

   ```bash
   sudo systemctl status hostapd
   ```

   If `hostapd` is inactive or failed, devices cannot connect to the network at all.

2. Connect a phone or laptop to the `ee-game` WiFi to confirm the AP is broadcasting and DHCP is working. If you can connect and receive an IP in the `192.168.4.x` range, the AP is functional.

3. Check the ESP32 serial monitor (connect the device to a laptop via USB and open a serial monitor at 115200 baud). Look for WiFi connection errors, incorrect SSID or password messages, or WebSocket connection failures.

4. Check the backend logs for incoming WebSocket connection events (OP-002):

   ```bash
   sudo journalctl -u ee-game -f
   ```

   Power cycle a device and watch for `[WebSocket] Device connected` within 15 seconds.

**Resolution**

- **`hostapd` failed or inactive:**

  ```bash
  sudo systemctl restart hostapd
  sudo systemctl status hostapd
  ```

  If it fails to restart, check `/etc/hostapd/hostapd.conf` for syntax errors.

- **Devices connecting to wrong SSID/password:** Update the SSID and password in the device firmware configuration and reflash. Verify the `hostapd.conf` SSID and passphrase match what the firmware is configured to use.

- **Devices on the network but not appearing in the host UI:** The WebSocket endpoint may be unreachable. Confirm the backend is listening:

  ```bash
  sudo ss -tlnp | grep 8000
  ```

  From a device or phone on the `ee-game` WiFi, try:
  ```bash
  curl http://192.168.4.1:8000/health
  ```

  If this fails from the WiFi network but works from the Pi itself, check firewall rules (`sudo iptables -L`).

---

## Scenario 4 — A Device Disconnects Mid-Session

**Symptom**

During an active game session, a player's device shows as stale or disconnected in the host control panel. The player's ESP32 may have lost its WiFi connection or rebooted.

**Diagnosis**

Check the backend logs for a disconnect event:

```bash
sudo journalctl -u ee-game -n 50 --no-pager
```

Look for a line containing `[WebSocket] Device disconnected` or a stale-device event with the relevant device identifier (OP-002). Check the ESP32 serial monitor for WiFi drop messages if the device is accessible.

**Resolution**

The platform is designed to handle individual device disconnections without ending the session for other players (NFR-009, NFR-010). The session continues; the disconnected device's player is shown as inactive.

1. Wait up to 30 seconds. The ESP32 firmware will attempt to reconnect automatically. If it succeeds, the device will re-register and resume participation.

2. If the device does not reconnect after 30 seconds, power cycle the ESP32 (unplug and replug its USB cable or press its reset button). Allow another 15 seconds for reconnection.

3. If the device still does not appear, check that it is within range of the WiFi access point and that the AP is still running (`sudo systemctl status hostapd`).

4. The game session does not need to be paused for a single device reconnection. However, if the host chooses to pause while the device reconnects, use the Pause control in the host panel.

---

## Scenario 5 — Application Crashes Repeatedly

**Symptom**

`sudo systemctl status ee-game` shows the service repeatedly restarting (`auto-restart` state) or has entered the `failed` state after multiple crash attempts. The service may briefly appear active before crashing again.

**Diagnosis**

Retrieve a longer log excerpt to find the Python traceback:

```bash
sudo journalctl -u ee-game -n 200 --no-pager
```

Look for a Python traceback — a block of lines starting with `Traceback (most recent call last):` followed by indented lines and an exception type at the end (for example, `ValueError`, `FileNotFoundError`, `sqlite3.DatabaseError`). The final line of the traceback identifies the root cause.

Common crash causes:

| Exception or message | Likely cause |
|---|---|
| `sqlite3.DatabaseError: database disk image is malformed` | The SQLite database file is corrupt (possibly due to an interrupted write during a power loss) |
| `FileNotFoundError` for a data or config file | A required file was deleted or moved |
| `ValidationError` from pydantic | The `.env` file contains an invalid value |
| `PermissionError` on a data directory | File system permissions changed |

**Resolution**

1. Stop the service to prevent further crash cycles:

   ```bash
   sudo systemctl stop ee-game
   ```

2. Note the full traceback from the logs. If reporting the issue, include the output of:

   ```bash
   sudo journalctl -u ee-game -n 200 --no-pager
   ```

3. Do not restart the service if it crashes immediately on start — doing so risks further data corruption if the issue involves a database or file write.

4. For a corrupt SQLite database: check whether a backup exists. If a backup is available from before the corruption, restore it:

   ```bash
   cp /opt/ee-game/host/backend/data/ee-game.db /opt/ee-game/host/backend/data/ee-game.db.corrupt
   cp ~/ee-game-data-bak/ee-game.db /opt/ee-game/host/backend/data/ee-game.db
   ```

5. For a `.env` validation error: open the file and correct the invalid value:

   ```bash
   sudo -u ee-game nano /opt/ee-game/host/backend/.env
   ```

6. After resolving the underlying cause, reset and start the service:

   ```bash
   sudo systemctl reset-failed ee-game
   sudo systemctl start ee-game
   sudo journalctl -u ee-game -n 20 --no-pager
   ```

---

## Scenario 6 — Host Pi Loses Power Mid-Session

**Symptom**

The Pi loses power (power cut, cable pulled, battery depleted) while a session is active. After power is restored, the application is not running.

**Diagnosis**

The `ee-game` service is configured with `WantedBy=multi-user.target` and is enabled, so systemd will start it automatically on boot. After power is restored and the Pi completes its boot sequence (30–60 seconds), the service should be active.

Check the service state after boot:

```bash
sudo systemctl status ee-game
```

If the service is running, check whether it recovered cleanly:

```bash
sudo journalctl -u ee-game -b --no-pager | head -40
```

Look for the startup log lines confirming the server is listening.

**Resolution**

1. If the service started automatically and is running — no action required. Proceed to check the session state in the host control panel.

2. If the service failed to start after boot, follow the steps in Scenario 1.

3. Session recovery after power loss (SRS Section 13.3, NFR-007): the platform persists session state to SQLite. A session that was in progress at the time of power loss will appear as a resumable saved session in the host control panel. The host selects it and resumes from the last persisted state.

4. If the session cannot be resumed due to database corruption, see Scenario 5 for diagnosis of `sqlite3.DatabaseError`.

5. Finished (archived) sessions survive power loss as immutable records and remain accessible from the host panel after recovery (SRS Section 13.3).
