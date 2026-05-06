# Pre-Event Smoke Test Checklist

**SRS references:** Section 13.1 (Deployment), Section 13.2 (Logging and Diagnostics), AC-011, NFR-007, NFR-010, OP-004
**Epic:** EP-01 — Platform Foundation
**User story:** EP-01-US-03

Run this checklist before every live session. Complete all checks in order. Each item has a pass criterion — if a check fails, follow the recovery note before proceeding. Do not begin a session until all checks pass.

Allow approximately 10 minutes to complete the full checklist.

---

## Checklist

### Check 1 — Service is active

**Command:**

```bash
systemctl is-active ee-game
```

**Pass criterion:** Output is exactly `active`.

**If it fails:** Run `sudo systemctl status ee-game` to see the current state. If the status is `failed`, reset and start:

```bash
sudo systemctl reset-failed ee-game
sudo systemctl start ee-game
```

Wait 10 seconds, then re-run the check. If the service fails again, consult `recovery-runbook.md` Scenario 1.

---

### Check 2 — Health endpoint responds

**Command:**

```bash
curl http://localhost:8000/health
```

**Pass criterion:** Response is `{"status": "ok"}` with HTTP 200.

**If it fails:** The service may be starting up — wait 10 seconds and retry. If it still fails, check logs:

```bash
sudo journalctl -u ee-game -n 30 --no-pager
```

Consult `recovery-runbook.md` Scenario 1.

---

### Check 3 — Public display URL loads

**Action:** On a browser connected to the `ee-game` WiFi, open:

```
http://192.168.4.1:8000/display
```

**Pass criterion:** The page loads fully without a white screen, 404 error, or browser console errors. The EE-Game public display UI is visible.

**If it fails:** Confirm `host/frontend/dist/` exists on the Pi:

```bash
ls /opt/ee-game/host/frontend/dist/
```

If the directory is missing or empty, the frontend must be copied from the build machine. See `raspberry-pi-setup.md` Step 6 in the Updating section.

---

### Check 4 — Host control URL loads

**Action:** On the same browser, open:

```
http://192.168.4.1:8000/host
```

**Pass criterion:** The host control panel loads without errors. Navigation controls and session management options are visible.

**If it fails:** Same diagnosis as Check 3. Also check the browser console for JavaScript errors (F12 → Console tab).

---

### Check 5 — WiFi access point is visible

**Action:** On a phone or laptop that is not already connected to the Pi, open the WiFi settings and scan for available networks.

**Pass criterion:** The `ee-game` SSID appears in the list. Connecting to it with the configured password succeeds and the device receives an IP address in the `192.168.4.x` range.

**If it fails:** Check `hostapd` and `dnsmasq`:

```bash
sudo systemctl status hostapd
sudo systemctl status dnsmasq
```

If either is inactive, restart it:

```bash
sudo systemctl restart hostapd dnsmasq
```

Wait 15 seconds and re-scan. If the SSID still does not appear, check `/etc/hostapd/hostapd.conf` for configuration errors and consult `recovery-runbook.md` Scenario 3.

---

### Check 6 — A test ESP32 device appears in the host UI

**Action:** Power on a test ESP32 device. Wait up to 30 seconds for it to connect to the `ee-game` WiFi and register with the backend.

**Pass criterion:** The device appears in the host control panel at `http://192.168.4.1:8000/host` with a connected status indicator. The device count changes from 0 to 1.

**If it fails:** Check backend logs for connection events:

```bash
sudo journalctl -u ee-game -f
```

Power cycle the device and watch for `[WebSocket] Device connected` in the log. If no event appears, the device is not reaching the backend — check the device's serial monitor for WiFi or connection errors. See `recovery-runbook.md` Scenario 3.

---

### Check 7 — Device shows connected LED status

**Action:** Observe the test ESP32 device's LED after it connects.

**Pass criterion:** The device LED shows the solid "connected" state as defined in the firmware specification. This confirms the device has successfully registered and is receiving state from the backend.

**If it fails:** If the LED is blinking in an error pattern or is off, check the device serial monitor (115200 baud) for firmware error messages. The device may have connected to the network but failed at the WebSocket registration step.

---

### Check 8 — Heartbeat log lines appear for the connected device

**Action:** With the test device connected, run:

```bash
sudo journalctl -u ee-game -f
```

**Pass criterion:** Within 30–60 seconds of the device connecting, heartbeat events appear in the log for that device. The backend logs device liveness transitions (OP-002).

**If it fails:** The device may have connected but stopped sending heartbeats. Power cycle the device. If heartbeats still do not appear, check the firmware heartbeat interval configuration and confirm `HEARTBEAT_TIMEOUT_SECONDS` in `.env` is set correctly (default: 30).

---

### Check 9 — No ERROR or CRITICAL log entries in the last 30 seconds

**Command:**

```bash
sudo journalctl -u ee-game --since "30 seconds ago" --no-pager
```

**Pass criterion:** The output contains no lines with the words `ERROR` or `CRITICAL`. INFO-level lines about server startup and device connections are normal and expected.

**If it fails:** Read the error message carefully. Common non-blocking errors that appear at startup (before any session begins) may be acceptable with a known cause. Errors related to session state, database writes, or WebSocket broadcasting should be investigated before starting a session. Consult `recovery-runbook.md` as appropriate.

---

### Check 10 — Sufficient disk space

**Command:**

```bash
df -h /
```

**Pass criterion:** The `Use%` column for the root filesystem (`/`) shows less than 90% used, and the `Avail` column shows at least 1 GB free.

**If it fails:** Identify large files consuming disk space:

```bash
du -sh /opt/ee-game/host/backend/data/
du -sh /var/log/journal/
```

Old journal logs can be cleared safely:

```bash
sudo journalctl --vacuum-size=100M
```

If the database is unexpectedly large, investigate before clearing anything.

---

### Check 11 — System time is correct

**Command:**

```bash
timedatectl status
```

**Pass criterion:** The local time shown matches the current real-world time within a few minutes. If the Pi was configured with NTP, the `NTP service: active` and `System clock synchronized: yes` lines should be present.

**Why this matters:** Log timestamps are used for post-event debugging (OP-005). Incorrect system time makes log correlation difficult. Session timestamps stored in SQLite (EP-02, EP-08) will also be wrong.

**If it fails:** If NTP is available (connected to a network with internet access during setup), enable it:

```bash
sudo timedatectl set-ntp true
```

If operating fully offline, set the time manually:

```bash
sudo timedatectl set-time "YYYY-MM-DD HH:MM:SS"
```

---

### Check 12 — Prior session data is accessible (if applicable)

**Action:** If a session was saved from a previous event, open the host control panel at `http://192.168.4.1:8000/host` and navigate to the session management area.

**Pass criterion:** Previously saved sessions appear in the session list and can be selected for resumption. Finished (archived) sessions are visible and distinguished from resumable sessions (SRS Section 13.3, NFR-007).

**If this check is not applicable** (no prior sessions exist): mark as N/A and proceed.

**If it fails:** Check whether the SQLite database file is present:

```bash
ls /opt/ee-game/host/backend/data/
```

If the database is missing, session data cannot be recovered. If the database is present but sessions do not appear in the UI, check the backend logs for database read errors. See `recovery-runbook.md` Scenario 5.

---

## Sign-Off

Record the result of each check (Pass / Fail / N/A) before starting the event. If any check failed and was not resolved, document the outstanding issue and the decision to proceed or abort.

| Check | Description | Result | Notes |
|---|---|---|---|
| 1 | Service is active | | |
| 2 | Health endpoint responds | | |
| 3 | Public display URL loads | | |
| 4 | Host control URL loads | | |
| 5 | WiFi access point visible | | |
| 6 | Test device appears in host UI | | |
| 7 | Device connected LED status | | |
| 8 | Heartbeat log lines present | | |
| 9 | No ERROR/CRITICAL in recent logs | | |
| 10 | Disk space adequate (>1 GB free) | | |
| 11 | System time is correct | | |
| 12 | Prior session data accessible (if applicable) | | |

**Operator:** __________________________ **Date:** __________________________
