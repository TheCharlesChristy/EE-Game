#!/usr/bin/env bash
# install-pi.sh — Install EE-Game onto a Raspberry Pi.
#
# Builds the frontend, installs the backend, configures the WiFi access point,
# installs the systemd service, starts it, and runs a smoke test.
#
# Run install-deps.sh first if this is a fresh system.
# This script is idempotent — re-running updates the app without touching the
# database or existing .env.
#
# Usage: sudo ./install-pi.sh --wifi-ssid <SSID> --wifi-password <passphrase>

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
INSTALL_DIR="/opt/ee-game"
PORT=8000
WIFI_SSID="ee-game"
WIFI_CHANNEL=7
WIFI_PASSWORD=""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'

info()  { echo -e "${GREEN}✓${NC}  $*"; }
warn()  { echo -e "${YELLOW}!${NC}  $*"; }
error() { echo -e "${RED}✗${NC}  $*" >&2; }
step()  { echo -e "\n${BOLD}── $* ──${NC}"; }

usage() {
    cat <<EOF
Usage: sudo $(basename "$0") [OPTIONS]

Installs EE-Game onto this Raspberry Pi in production mode: builds the
frontend, installs the backend, sets up the WiFi access point, installs and
starts the systemd service, and runs a smoke test.

Run install-deps.sh first on a fresh system.

Options:
      --wifi-ssid SSID      WiFi network name devices connect to  (default: ee-game)
      --wifi-password PASS  WiFi passphrase, min 8 chars          (prompted if omitted)
      --wifi-channel N      WiFi channel                          (default: 7)
  -p, --port PORT           Backend port                          (default: 8000)
  -d, --install-dir DIR     Installation directory                (default: /opt/ee-game)
  -h, --help                Show this help and exit

Examples:
  sudo ./install-pi.sh --wifi-ssid "Physics Lab" --wifi-password "circuits2024"
  sudo ./install-pi.sh --wifi-ssid "EE-Game" --wifi-password "circuits2024" --port 9000
EOF
}

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --wifi-ssid)     WIFI_SSID="$2";     shift 2 ;;
        --wifi-password) WIFI_PASSWORD="$2"; shift 2 ;;
        --wifi-channel)  WIFI_CHANNEL="$2";  shift 2 ;;
        -p|--port)       PORT="$2";          shift 2 ;;
        -d|--install-dir) INSTALL_DIR="$2";  shift 2 ;;
        -h|--help)       usage; exit 0 ;;
        *) error "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ── Preflight ─────────────────────────────────────────────────────────────────
[[ "$EUID" -eq 0 ]] || { error "Run with sudo: sudo $0 $*"; exit 1; }

[[ -f "$ROOT_DIR/host/backend/pyproject.toml" ]] || {
    error "Run from the root of the EE-Game repository."
    exit 1
}

command -v python3 &>/dev/null || { error "python3 not found — run install-deps.sh first."; exit 1; }
command -v npm     &>/dev/null || { error "npm not found — run install-deps.sh first."; exit 1; }
command -v hostapd &>/dev/null || { error "hostapd not found — run install-deps.sh first."; exit 1; }

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' || {
    error "Python 3.12+ required. Found: $(python3 --version). Run install-deps.sh first."
    exit 1
}

# Prompt for WiFi password if not provided
if [[ -z "$WIFI_PASSWORD" ]]; then
    while true; do
        read -rsp "WiFi passphrase for '$WIFI_SSID' (min 8 chars): " WIFI_PASSWORD; echo
        [[ ${#WIFI_PASSWORD} -ge 8 ]] && break
        warn "Passphrase must be at least 8 characters."
    done
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

# Create service user if needed
if ! id "ee-game" &>/dev/null; then
    useradd --system --shell /bin/false --home "$INSTALL_DIR" ee-game
fi

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

# ── Step 5: Environment file ──────────────────────────────────────────────────
step "Writing configuration"
ENV_FILE="$INSTALL_DIR/host/backend/.env"
if [[ -f "$ENV_FILE" ]]; then
    warn ".env already exists — not overwritten. Edit $ENV_FILE to change settings."
else
    sudo -u ee-game tee "$ENV_FILE" > /dev/null <<EOF
BACKEND_HOST=0.0.0.0
BACKEND_PORT=$PORT
LOG_LEVEL=WARNING
HEARTBEAT_TIMEOUT_SECONDS=30
STATIC_FILES_DIR=../../frontend/dist
WIFI_SSID=$WIFI_SSID
WIFI_PASSWORD=$WIFI_PASSWORD
BACKEND_AP_HOST=192.168.4.1
EOF
    chmod 600 "$ENV_FILE"
    info "Config written to $ENV_FILE"
fi

# ── Step 6: systemd service ───────────────────────────────────────────────────
step "Installing systemd service"
sed "s|--port [0-9]*|--port $PORT|g" \
    "$INSTALL_DIR/docs/deployment/ee-game.service" \
    > /etc/systemd/system/ee-game.service
systemctl daemon-reload
systemctl enable ee-game.service
info "Service installed and enabled"

# ── Step 7: ee-game CLI ───────────────────────────────────────────────────────
ln -sf "$INSTALL_DIR/ee-game" /usr/local/bin/ee-game
chmod +x "$INSTALL_DIR/ee-game"
info "ee-game CLI available at /usr/local/bin/ee-game"

# ── Step 8: WiFi access point ─────────────────────────────────────────────────
step "Configuring WiFi access point"
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

grep -q 'dhcp-range=192.168.4' /etc/dnsmasq.conf 2>/dev/null || \
    printf '\ninterface=wlan0\ndhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,24h\n' >> /etc/dnsmasq.conf

grep -q 'static ip_address=192.168.4.1' /etc/dhcpcd.conf 2>/dev/null || \
    printf '\ninterface wlan0\nstatic ip_address=192.168.4.1/24\nnohook wpa_supplicant\n' >> /etc/dhcpcd.conf

systemctl unmask hostapd
systemctl enable hostapd dnsmasq
info "WiFi AP configured (SSID: $WIFI_SSID)"

# ── Step 9: Start service and smoke test ──────────────────────────────────────
step "Starting service"
systemctl start ee-game
sleep 3

if EE_GAME_URL="http://localhost:$PORT" bash "$ROOT_DIR/scripts/smoke-test.sh"; then
    info "Smoke test passed"
else
    error "Smoke test failed — check logs: journalctl -u ee-game -n 50"
    exit 1
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo
echo -e "${GREEN}Installation complete.${NC}"
echo
echo "  Service  : running (sudo ee-game status)"
echo "  Logs     : sudo ee-game logs -f"
echo
echo "  Reboot the Pi to activate the WiFi access point, then:"
echo "    WiFi SSID : $WIFI_SSID"
echo "    Host UI   : http://192.168.4.1:$PORT/host"
echo "    Display   : http://192.168.4.1:$PORT/display"
echo
echo "  Flash an ESP32: ee-game flash"
echo
