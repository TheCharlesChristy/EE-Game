#!/usr/bin/env bash
# install-pi.sh — Install EE-Game onto a Raspberry Pi.
#
# All configuration is read from .env in the repository root.
# Edit that file before running this script.
#
# Run install-deps.sh first on a fresh system.
# This script is idempotent — re-running updates the app without touching the
# existing database or installed .env.
#
# Usage: sudo ./install-pi.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT_DIR/.env"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
info()  { echo -e "${GREEN}✓${NC}  $*"; }
warn()  { echo -e "${YELLOW}!${NC}  $*"; }
error() { echo -e "${RED}✗${NC}  $*" >&2; }
step()  { echo -e "\n${BOLD}── $* ──${NC}"; }

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    cat <<EOF
Usage: sudo $(basename "$0")

Installs EE-Game onto this Raspberry Pi. All configuration is read from .env
in the repository root — edit that file before running.

Run install-deps.sh first on a fresh system.
EOF
    exit 0
fi

# ── Preflight ─────────────────────────────────────────────────────────────────
[[ "$EUID" -eq 0 ]] || { error "Run with sudo: sudo $0"; exit 1; }

[[ -f "$ENV_FILE" ]] || { error ".env not found at $ENV_FILE"; exit 1; }

[[ -f "$ROOT_DIR/host/backend/pyproject.toml" ]] || {
    error "Run from the root of the EE-Game repository."
    exit 1
}

command -v python3 &>/dev/null || { error "python3 not found — run install-deps.sh first."; exit 1; }
command -v npm     &>/dev/null || { error "npm not found — run install-deps.sh first."; exit 1; }
command -v hostapd &>/dev/null || { error "hostapd not found — run install-deps.sh first."; exit 1; }

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' || {
    error "Python 3.12+ required. Found: $(python3 --version)"
    exit 1
}

# ── Load configuration ────────────────────────────────────────────────────────
# Source the .env, skipping blank lines and comments
set -a
# shellcheck disable=SC1090
source <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$')
set +a

# Required values
: "${BACKEND_PORT:?BACKEND_PORT not set in .env}"
: "${WIFI_SSID:?WIFI_SSID not set in .env}"
: "${WIFI_PASSWORD:?WIFI_PASSWORD not set in .env}"
: "${BACKEND_AP_HOST:?BACKEND_AP_HOST not set in .env}"

[[ ${#WIFI_PASSWORD} -ge 8 ]] || { error "WIFI_PASSWORD must be at least 8 characters."; exit 1; }

INSTALL_DIR="${INSTALL_DIR:-/opt/ee-game}"
WIFI_CHANNEL="${WIFI_CHANNEL:-7}"

echo
echo -e "${BOLD}EE-Game installation${NC}"
echo "  Config      : $ENV_FILE"
echo "  Install dir : $INSTALL_DIR"
echo "  Port        : $BACKEND_PORT"
echo "  WiFi SSID   : $WIFI_SSID"
echo "  AP host     : $BACKEND_AP_HOST"
echo

# ── Stop any running instance ────────────────────────────────────────────────
# Prevents port conflicts and file-in-use errors during rsync.
if systemctl is-active --quiet ee-game 2>/dev/null; then
    step "Stopping running service"
    systemctl stop ee-game
    info "Service stopped"
fi

# ── Step 1: Build frontend ────────────────────────────────────────────────────
step "Building frontend"
cd "$ROOT_DIR/host/frontend"
npm install --silent
npm run build
info "Frontend built"

# ── Step 2: Copy application files ───────────────────────────────────────────
step "Installing application to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

id "ee-game" &>/dev/null || useradd --system --shell /bin/false --home "$INSTALL_DIR" ee-game

rsync -a --delete \
    --exclude='.git/' \
    --exclude='host/backend/.venv/' \
    --exclude='host/backend/data/' \
    --exclude='host/backend/.env' \
    --exclude='host/frontend/node_modules/' \
    --exclude='firmware/.pio/' \
    "$ROOT_DIR/" "$INSTALL_DIR/"
chown -R ee-game:ee-game "$INSTALL_DIR"
info "Files copied"

# ── Step 3: Python virtual environment ───────────────────────────────────────
step "Setting up Python environment"
VENV="$INSTALL_DIR/host/backend/.venv"
[[ -d "$VENV" ]] || sudo -u ee-game python3 -m venv "$VENV"
sudo -u ee-game "$VENV/bin/pip" install --quiet -e "$INSTALL_DIR/host/backend"
info "Python environment ready"

# ── Step 4: Data directory ────────────────────────────────────────────────────
sudo -u ee-game mkdir -p "$INSTALL_DIR/host/backend/data"

# ── Step 5: Install .env ──────────────────────────────────────────────────────
step "Writing configuration"
INSTALLED_ENV="$INSTALL_DIR/host/backend/.env"
if [[ -f "$INSTALLED_ENV" ]]; then
    warn ".env already exists at $INSTALLED_ENV — not overwritten."
    warn "Edit it directly and run 'ee-game restart' to apply changes."
else
    install -o ee-game -g ee-game -m 600 "$ENV_FILE" "$INSTALLED_ENV"
    info "Config installed"
fi

# ── Step 6: systemd service ───────────────────────────────────────────────────
step "Installing systemd service"
sed "s|--port [0-9]*|--port $BACKEND_PORT|g" \
    "$INSTALL_DIR/docs/deployment/ee-game.service" \
    > /etc/systemd/system/ee-game.service
systemctl daemon-reload
systemctl enable ee-game.service
info "Service installed and enabled"

# ── Step 7: ee-game CLI ───────────────────────────────────────────────────────
ln -sf "$INSTALL_DIR/ee-game" /usr/local/bin/ee-game
chmod +x "$INSTALL_DIR/ee-game"
info "ee-game CLI → /usr/local/bin/ee-game"

# ── Step 8: WiFi access point ─────────────────────────────────────────────────
step "Configuring WiFi access point"

# Write hostapd config
tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=wlan0
driver=nl80211
ssid=$WIFI_SSID
hw_mode=g
channel=$WIFI_CHANNEL
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$WIFI_PASSWORD
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF
grep -q 'DAEMON_CONF' /etc/default/hostapd 2>/dev/null || \
    echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >> /etc/default/hostapd

# Write dnsmasq config in a drop-in file (idempotent on re-run)
tee /etc/dnsmasq.d/ee-game.conf > /dev/null <<EOF
interface=wlan0
dhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,24h
EOF

# Detect network management stack.
# Pi OS Bookworm defaults to NetworkManager; we must unmanage wlan0 so hostapd can run.
if systemctl is-active --quiet NetworkManager 2>/dev/null; then
    info "NetworkManager detected — marking wlan0 as unmanaged"
    mkdir -p /etc/NetworkManager/conf.d
    tee /etc/NetworkManager/conf.d/99-ee-game.conf > /dev/null <<EOF
[keyfile]
unmanaged-devices=interface-name:wlan0
EOF
    if command -v nmcli &>/dev/null; then
        nmcli device set wlan0 managed no 2>/dev/null || true
    else
        systemctl reload NetworkManager 2>/dev/null || true
    fi
    sleep 1
else
    # dhcpcd — add static IP config and restart
    grep -q 'static ip_address=192.168.4.1' /etc/dhcpcd.conf 2>/dev/null || \
        printf '\ninterface wlan0\nstatic ip_address=192.168.4.1/24\nnohook wpa_supplicant\n' >> /etc/dhcpcd.conf
    systemctl restart dhcpcd 2>/dev/null || true
    sleep 2
fi

# Assign static IP to wlan0 immediately (effective without reboot)
ip addr show wlan0 2>/dev/null | grep -q "192.168.4.1" || \
    ip addr add 192.168.4.1/24 dev wlan0 2>/dev/null || true
ip link set wlan0 up 2>/dev/null || true

# Enable and start AP services now (not just at next boot)
systemctl unmask hostapd
systemctl enable hostapd dnsmasq
systemctl restart dnsmasq
systemctl restart hostapd
sleep 3

# Verify the AP is actually broadcasting
AP_UP=false
for _i in 1 2 3 4 5; do
    if iw dev wlan0 info 2>/dev/null | grep -q "type AP"; then
        AP_UP=true; break
    fi
    sleep 2
done

if [[ "$AP_UP" == true ]]; then
    info "WiFi AP is broadcasting (SSID: $WIFI_SSID)"
else
    warn "WiFi AP did not start yet — check: journalctl -u hostapd -n 30"
    warn "A reboot may be required if the network stack has not fully applied."
fi

# ── Step 9: Start service and smoke test ──────────────────────────────────────
step "Starting service"
systemctl start ee-game
sleep 3

if EE_GAME_URL="http://localhost:$BACKEND_PORT" bash "$ROOT_DIR/scripts/smoke-test.sh"; then
    info "Smoke test passed"
else
    error "Smoke test failed — check logs: journalctl -u ee-game -n 50"
    exit 1
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo
echo -e "${GREEN}Installation complete.${NC}"
echo
echo "  Service : running  (ee-game status)"
echo "  Logs    : ee-game logs -f"
echo
echo "  Reboot to activate the WiFi access point, then:"
echo "    WiFi SSID : $WIFI_SSID"
echo "    Host UI   : http://$BACKEND_AP_HOST:$BACKEND_PORT/host"
echo "    Display   : http://$BACKEND_AP_HOST:$BACKEND_PORT/display"
echo
echo "  Flash an ESP32: ee-game flash"
echo
