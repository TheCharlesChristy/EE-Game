#!/usr/bin/env bash
# install.sh — Install EE-Game on a Raspberry Pi.
#
# One command does everything: packages, backend, frontend, service, and WiFi.
# Safe to re-run — it picks up where it left off.
#
# Usage: sudo ./install.sh

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_ENV="$ROOT_DIR/.env"
ENV_FILE="$ROOT_DIR/host/backend/.env"
VENV="$ROOT_DIR/host/backend/.venv"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
PROBLEMS=()   # things that need manual attention; printed at end

ok()      { echo -e "    ${GREEN}✓${NC}  $*"; }
skip()    { echo -e "    ${GREEN}✓${NC}  $* (already done)"; }
problem() { echo -e "    ${YELLOW}!${NC}  $*"; PROBLEMS+=("$*"); }
die()     { echo -e "\n  ${RED}Error:${NC} $*\n" >&2; exit 1; }
banner()  { echo; echo -e "${BOLD}${1}${NC}"; echo; }
step()    { echo; echo -e "  ${BOLD}── $* ──${NC}"; }

# ─────────────────────────────────────────────────────────────────────────────
#  PRE-FLIGHT CHECKS
# ─────────────────────────────────────────────────────────────────────────────
banner "EE-Game Installer"

[[ "$EUID" -eq 0 ]] \
    || die "Please run as:  sudo ./install.sh"

SERVICE_USER="${SUDO_USER:-}" \
    || die "Run with 'sudo ./install.sh', not as root directly."
[[ -n "$SERVICE_USER" ]] \
    || die "Could not determine your username. Run: sudo ./install.sh"

[[ -f "$ROOT_DIR/host/backend/pyproject.toml" ]] \
    || die "Run this script from the root of the EE-Game repository."

[[ -f "$ROOT_ENV" ]] \
    || die ".env not found. Copy .env.example to .env and fill in your WiFi details, then re-run."

# Load .env values
set -a
source <(grep -v '^\s*#' "$ROOT_ENV" | grep -v '^\s*$') 2>/dev/null || true
set +a

[[ -n "${WIFI_SSID:-}"     ]] || die "WIFI_SSID is missing from .env"
[[ -n "${WIFI_PASSWORD:-}" ]] || die "WIFI_PASSWORD is missing from .env"
[[ ${#WIFI_PASSWORD} -ge 8 ]] || die "WIFI_PASSWORD must be at least 8 characters"
BACKEND_PORT="${BACKEND_PORT:-8000}"
BACKEND_AP_HOST="${BACKEND_AP_HOST:-192.168.4.1}"

echo "  Installing from  :  $ROOT_DIR"
echo "  Running as user  :  $SERVICE_USER"
echo "  Game WiFi name   :  $WIFI_SSID"
echo "  Backend address  :  http://$BACKEND_AP_HOST:$BACKEND_PORT"
echo

# Detect package manager
if   command -v apt-get &>/dev/null; then PKG_MANAGER="apt"
elif command -v dnf     &>/dev/null; then PKG_MANAGER="dnf"
elif command -v yum     &>/dev/null; then PKG_MANAGER="yum"
else die "No supported package manager found (need apt, dnf, or yum)."
fi

pkg_install() {
    case "$PKG_MANAGER" in
        apt)     apt-get install -y --no-install-recommends "$@" &>/dev/null ;;
        dnf|yum) "$PKG_MANAGER" install -y "$@" &>/dev/null ;;
    esac
}

# ─────────────────────────────────────────────────────────────────────────────
#  1. SYSTEM PACKAGES
#  All downloads happen here, before touching WiFi.
# ─────────────────────────────────────────────────────────────────────────────
step "1 of 6 — System packages"

case "$PKG_MANAGER" in
    apt)     apt-get update -qq ;;
    dnf|yum) "$PKG_MANAGER" makecache -q ;;
esac

pkg_install git curl ca-certificates unzip 2>/dev/null || true

# Python — try newest version available from the package manager
PYTHON_BIN=""
for ver in 3.15 3.14 3.13 3.12; do
    if command -v "python${ver}" &>/dev/null; then
        PYTHON_BIN="python${ver}"; break
    fi
    case "$PKG_MANAGER" in
        apt)
            if apt-get install -y --no-install-recommends \
                   "python${ver}" "python${ver}-venv" "python${ver}-dev" &>/dev/null 2>&1; then
                PYTHON_BIN="python${ver}"; break
            fi ;;
        dnf|yum)
            if "$PKG_MANAGER" install -y "python${ver}" "python${ver}-devel" &>/dev/null 2>&1; then
                PYTHON_BIN="python${ver}"; break
            fi ;;
    esac
done

if [[ -z "$PYTHON_BIN" ]]; then
    pkg_install python3 python3-venv 2>/dev/null || true
    if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; then
        PYTHON_BIN="python3"
    fi
fi

if [[ -z "$PYTHON_BIN" ]]; then
    die "Python 3.12 or newer is required but could not be installed automatically.
  Install it manually (e.g. sudo apt install python3.13) then re-run this script."
fi
if ! "${PYTHON_BIN}" -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; then
    die "Python 3.12+ required. Found $("${PYTHON_BIN}" --version 2>&1).
  Install a newer Python (e.g. sudo apt install python3.13) then re-run."
fi

# Register with update-alternatives so 'python3' points at our version
if [[ "$PYTHON_BIN" != "python3" ]] && command -v update-alternatives &>/dev/null; then
    update-alternatives --install /usr/bin/python3 python3 \
        "$(command -v "${PYTHON_BIN}")" 10 2>/dev/null || true
fi
ok "Python: $("${PYTHON_BIN}" --version)"

# Node.js (needed to build the web frontend)
NODE_MAJOR="$(node --version 2>/dev/null | grep -oE '^v[0-9]+' | tr -d 'v' || echo 0)"
if [[ "$NODE_MAJOR" -lt 18 ]]; then
    pkg_install nodejs npm 2>/dev/null || true
    NODE_MAJOR="$(node --version 2>/dev/null | grep -oE '^v[0-9]+' | tr -d 'v' || echo 0)"
fi
if [[ "$NODE_MAJOR" -ge 18 ]]; then
    ok "Node.js: $(node --version)"
else
    problem "Node.js 18+ is not installed (found v${NODE_MAJOR}). The web UI will not work until you install it: sudo apt install nodejs"
fi

# mDNS — makes the Pi reachable at its-hostname.local on the network
pkg_install avahi-daemon 2>/dev/null || true
case "$PKG_MANAGER" in
    apt)     pkg_install libnss-mdns 2>/dev/null || true ;;
    dnf|yum) pkg_install nss-mdns    2>/dev/null || true ;;
esac
systemctl enable --now avahi-daemon 2>/dev/null || true
ok "mDNS: Pi reachable at $(hostname).local"

# USB serial group (needed only for flashing ESP32 devices from this Pi)
if ! id -nG "$SERVICE_USER" 2>/dev/null | grep -qw dialout; then
    usermod -aG dialout "$SERVICE_USER" 2>/dev/null && \
        ok "Added $SERVICE_USER to dialout group (for ESP32 flashing)" || true
fi
cat > /etc/udev/rules.d/99-esp32.rules <<'EOF'
SUBSYSTEM=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", GROUP="dialout"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="55d4", MODE="0666", GROUP="dialout"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0666", GROUP="dialout"
EOF
udevadm control --reload-rules 2>/dev/null || true

# ─────────────────────────────────────────────────────────────────────────────
#  2. BUILD WEB FRONTEND
# ─────────────────────────────────────────────────────────────────────────────
step "2 of 6 — Building web frontend"

if [[ "$NODE_MAJOR" -ge 18 ]]; then
    if sudo -u "$SERVICE_USER" bash -c \
           "cd '$ROOT_DIR/host/frontend' && npm install --silent && npm run build" 2>/dev/null; then
        ok "Frontend built"
    else
        problem "Frontend build failed. Run this manually to see the error:
    cd $ROOT_DIR/host/frontend && npm install && npm run build"
    fi
else
    problem "Frontend build skipped — Node.js not available"
fi

# ─────────────────────────────────────────────────────────────────────────────
#  3. PYTHON BACKEND
# ─────────────────────────────────────────────────────────────────────────────
step "3 of 6 — Setting up backend"

[[ -d "$VENV" ]] || sudo -u "$SERVICE_USER" "${PYTHON_BIN}" -m venv "$VENV"

if sudo -u "$SERVICE_USER" "$VENV/bin/pip" install --quiet -e "$ROOT_DIR/host/backend" 2>/dev/null; then
    ok "Backend dependencies installed"
else
    problem "Backend dependency install failed. Run manually:
    $VENV/bin/pip install -e $ROOT_DIR/host/backend"
fi

sudo -u "$SERVICE_USER" mkdir -p "$ROOT_DIR/host/backend/data"

# ─────────────────────────────────────────────────────────────────────────────
#  4. CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
step "4 of 6 — Configuration"

if [[ -f "$ENV_FILE" ]]; then
    skip "Config already at $ENV_FILE"
else
    sudo -u "$SERVICE_USER" cp "$ROOT_ENV" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    ok "Config written"
fi

# ─────────────────────────────────────────────────────────────────────────────
#  5. SYSTEM SERVICE
# ─────────────────────────────────────────────────────────────────────────────
step "5 of 6 — System service"

systemctl stop ee-game 2>/dev/null || true

cat > /etc/systemd/system/ee-game.service <<EOF
[Unit]
Description=EE-Game Backend
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$ROOT_DIR/host/backend
EnvironmentFile=$ENV_FILE
ExecStart=$VENV/bin/uvicorn ee_game_backend.main:app --host 0.0.0.0 --port $BACKEND_PORT
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ee-game
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ee-game
systemctl start ee-game
sleep 3

if EE_GAME_URL="http://localhost:$BACKEND_PORT" \
       bash "$ROOT_DIR/scripts/smoke-test.sh" &>/dev/null; then
    ok "Service started and healthy"
else
    problem "Service started but health check failed.
    Check what went wrong: journalctl -u ee-game -n 30"
fi

chmod +x "$ROOT_DIR/ee-game"
ln -sf "$ROOT_DIR/ee-game" /usr/local/bin/ee-game
ok "ee-game command installed"

# ─────────────────────────────────────────────────────────────────────────────
#  6. WIFI ACCESS POINT
#
#  This step writes config and registers the AP to start on next boot.
#  It does NOT change your current network connection — you will not be
#  disconnected. The AP becomes active after you reboot.
# ─────────────────────────────────────────────────────────────────────────────
step "6 of 6 — WiFi access point"
echo "  (Your current network connection is not affected.)"
echo "  (The game WiFi activates after you reboot.)"
echo

AP_CONFIGURED=false

# ── Option A: NetworkManager (Ubuntu, Pi OS Bookworm) ────────────────────────
# NM manages WiFi natively — no hostapd or dnsmasq needed.
if command -v nmcli &>/dev/null && systemctl is-active --quiet NetworkManager 2>/dev/null; then
    nmcli connection delete ee-game-ap &>/dev/null || true

    if nmcli connection add \
            type wifi \
            ifname wlan0 \
            con-name ee-game-ap \
            ssid "$WIFI_SSID" \
            802-11-wireless.mode ap \
            802-11-wireless.band bg \
            ipv4.method shared \
            ipv4.addresses "$BACKEND_AP_HOST/24" \
            wifi-sec.key-mgmt wpa-psk \
            wifi-sec.psk "$WIFI_PASSWORD" \
            connection.autoconnect yes \
            connection.autoconnect-priority 100 &>/dev/null; then
        ok "WiFi AP profile registered with NetworkManager"
        ok "SSID '$WIFI_SSID' will broadcast after reboot"
        AP_CONFIGURED=true
    else
        echo "    nmcli failed — trying hostapd instead"
    fi
fi

# ── Option B: hostapd + dnsmasq (Pi OS Bullseye or no NetworkManager) ────────
if [[ "$AP_CONFIGURED" == false ]]; then
    if pkg_install hostapd dnsmasq 2>/dev/null; then
        mkdir -p /etc/hostapd
        cat > /etc/hostapd/hostapd.conf <<EOF
interface=wlan0
driver=nl80211
ssid="$WIFI_SSID"
hw_mode=g
channel=7
wpa=2
wpa_passphrase=$WIFI_PASSWORD
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF
        grep -q 'DAEMON_CONF' /etc/default/hostapd 2>/dev/null \
            || echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >> /etc/default/hostapd

        mkdir -p /etc/dnsmasq.d
        cat > /etc/dnsmasq.d/ee-game.conf <<EOF
interface=wlan0
dhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,24h
EOF
        # Static IP for wlan0 on next boot (dhcpcd, used by Pi OS)
        if [[ -f /etc/dhcpcd.conf ]]; then
            grep -q "static ip_address=$BACKEND_AP_HOST" /etc/dhcpcd.conf \
                || printf '\ninterface wlan0\nstatic ip_address=%s/24\nnohook wpa_supplicant\n' \
                          "$BACKEND_AP_HOST" >> /etc/dhcpcd.conf
        fi

        # Enable for boot — intentionally NOT starting now to preserve your connection
        systemctl unmask hostapd 2>/dev/null || true
        systemctl enable hostapd dnsmasq 2>/dev/null || true
        ok "WiFi AP configured via hostapd"
        ok "SSID '$WIFI_SSID' will broadcast after reboot"
        AP_CONFIGURED=true
    else
        problem "WiFi AP could not be configured (neither nmcli nor hostapd available).
    Install hostapd manually: sudo apt install hostapd dnsmasq"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
#  DONE
# ─────────────────────────────────────────────────────────────────────────────
echo
echo -e "  ${GREEN}${BOLD}Installation complete.${NC}"
echo

if [[ ${#PROBLEMS[@]} -gt 0 ]]; then
    echo -e "  ${YELLOW}${BOLD}Action required — these steps need manual attention:${NC}"
    for p in "${PROBLEMS[@]}"; do
        echo
        echo -e "  ${YELLOW}!${NC}  $p"
    done
    echo
fi

echo "  ┌─────────────────────────────────────────────────────┐"
echo "  │                    NEXT STEPS                       │"
echo "  ├─────────────────────────────────────────────────────┤"
echo "  │  1. Reboot the Pi:                                  │"
echo "  │       sudo reboot                                   │"
echo "  │                                                     │"
echo "  │  2. After reboot, connect your device to:           │"
printf "  │       WiFi: %-39s│\n" "$WIFI_SSID"
echo "  │                                                     │"
echo "  │  3. Open the host control panel at:                 │"
printf "  │       http://%-39s│\n" "$BACKEND_AP_HOST:$BACKEND_PORT/host"
echo "  └─────────────────────────────────────────────────────┘"
echo
echo "  Useful commands:"
echo "    ee-game status    — check if everything is running"
echo "    ee-game logs      — see what the backend is doing"
echo "    ee-game restart   — apply config changes"
echo
