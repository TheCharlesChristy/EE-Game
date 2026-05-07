#!/usr/bin/env bash
# install-pi.sh — Install EE-Game onto a Raspberry Pi.
#
# Run this from the root of the git clone. That directory becomes the
# installation — no files are copied elsewhere. Updates are:
#   git pull && ee-game restart
#
# Usage: sudo ./install-pi.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_ENV="$ROOT_DIR/.env"
ENV_FILE="$ROOT_DIR/host/backend/.env"
VENV="$ROOT_DIR/host/backend/.venv"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
info()  { echo -e "${GREEN}✓${NC}  $*"; }
warn()  { echo -e "${YELLOW}!${NC}  $*"; }
error() { echo -e "${RED}✗${NC}  $*" >&2; }
step()  { echo -e "\n${BOLD}── $* ──${NC}"; }

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    cat <<EOF
Usage: sudo $(basename "$0")

Installs EE-Game onto this Raspberry Pi. Run from the root of the git clone.

That directory becomes the installation — no files are copied elsewhere.
To update: git pull && ee-game restart

Edit .env before running to set WiFi credentials and backend port.
EOF
    exit 0
fi

# ── Preflight ─────────────────────────────────────────────────────────────────
[[ "$EUID" -eq 0 ]] || { error "Run with sudo: sudo $0"; exit 1; }

[[ -f "$ROOT_DIR/host/backend/pyproject.toml" ]] || {
    error "Run from the root of the EE-Game repository."
    exit 1
}

SERVICE_USER="${SUDO_USER:-}"
[[ -n "$SERVICE_USER" ]] || {
    error "Could not determine the installing user. Run with 'sudo ./install-pi.sh', not 'sudo su'."
    exit 1
}

[[ -f "$ROOT_ENV" ]] || { error ".env not found at $ROOT_ENV"; exit 1; }

command -v python3 &>/dev/null || { error "python3 not found — run install-deps.sh first."; exit 1; }
command -v npm     &>/dev/null || { error "npm not found — run install-deps.sh first."; exit 1; }
command -v hostapd &>/dev/null || { error "hostapd not found — run install-deps.sh first."; exit 1; }

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' || {
    error "Python 3.12+ required. Found: $(python3 --version)"
    exit 1
}

# ── Load configuration ────────────────────────────────────────────────────────
set -a
# shellcheck disable=SC1090
source <(grep -v '^\s*#' "$ROOT_ENV" | grep -v '^\s*$')
set +a

: "${BACKEND_PORT:?BACKEND_PORT not set in .env}"
: "${WIFI_SSID:?WIFI_SSID not set in .env}"
: "${WIFI_PASSWORD:?WIFI_PASSWORD not set in .env}"
: "${BACKEND_AP_HOST:?BACKEND_AP_HOST not set in .env}"
[[ ${#WIFI_PASSWORD} -ge 8 ]] || { error "WIFI_PASSWORD must be at least 8 characters."; exit 1; }

WIFI_CHANNEL="${WIFI_CHANNEL:-7}"

echo
echo -e "${BOLD}EE-Game installation${NC}"
echo "  Install dir  : $ROOT_DIR  (this git clone is the app)"
echo "  Service user : $SERVICE_USER"
echo "  Port         : $BACKEND_PORT"
echo "  WiFi SSID    : $WIFI_SSID"
echo "  AP host      : $BACKEND_AP_HOST"
echo

# ── Stop any running service ──────────────────────────────────────────────────
if systemctl is-active --quiet ee-game 2>/dev/null; then
    step "Stopping running service"
    systemctl stop ee-game
    sleep 2
    info "Service stopped"
fi

# ── Step 1: Build frontend ────────────────────────────────────────────────────
step "Building frontend"
sudo -u "$SERVICE_USER" bash -c "cd '$ROOT_DIR/host/frontend' && npm install --silent && npm run build"
info "Frontend built"

# ── Step 2: Python virtual environment ───────────────────────────────────────
step "Setting up Python environment"
[[ -d "$VENV" ]] || sudo -u "$SERVICE_USER" python3 -m venv "$VENV"
sudo -u "$SERVICE_USER" "$VENV/bin/pip" install --quiet -e "$ROOT_DIR/host/backend"
info "Python environment ready"

# ── Step 3: Data directory ────────────────────────────────────────────────────
sudo -u "$SERVICE_USER" mkdir -p "$ROOT_DIR/host/backend/data"

# ── Step 4: Live .env ─────────────────────────────────────────────────────────
step "Writing configuration"
if [[ -f "$ENV_FILE" ]]; then
    warn ".env already exists at $ENV_FILE — not overwritten."
    warn "Edit it directly, then run: ee-game restart"
else
    sudo -u "$SERVICE_USER" cp "$ROOT_ENV" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    info "Config installed at $ENV_FILE"
fi

# ── Step 5: systemd service (generated directly, no template needed) ──────────
step "Installing systemd service"
cat > /etc/systemd/system/ee-game.service <<EOF
[Unit]
Description=EE Game Backend
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
info "Service installed (runs as $SERVICE_USER from $ROOT_DIR)"

# ── Step 6: ee-game CLI ───────────────────────────────────────────────────────
chmod +x "$ROOT_DIR/ee-game"
ln -sf "$ROOT_DIR/ee-game" /usr/local/bin/ee-game
info "ee-game CLI → /usr/local/bin/ee-game → $ROOT_DIR/ee-game"

# ── Step 7: WiFi access point ─────────────────────────────────────────────────
step "Configuring WiFi access point"

tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=wlan0
driver=nl80211
ssid="$WIFI_SSID"
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

tee /etc/dnsmasq.d/ee-game.conf > /dev/null <<EOF
interface=wlan0
dhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,24h
EOF

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
    grep -q 'static ip_address=192.168.4.1' /etc/dhcpcd.conf 2>/dev/null || \
        printf '\ninterface wlan0\nstatic ip_address=192.168.4.1/24\nnohook wpa_supplicant\n' >> /etc/dhcpcd.conf
    systemctl restart dhcpcd 2>/dev/null || true
    sleep 2
fi

ip addr show wlan0 2>/dev/null | grep -q "192.168.4.1" || \
    ip addr add 192.168.4.1/24 dev wlan0 2>/dev/null || true
ip link set wlan0 up 2>/dev/null || true

systemctl unmask hostapd
systemctl enable hostapd dnsmasq
systemctl restart dnsmasq
systemctl restart hostapd
sleep 3

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

# ── Step 8: Start and smoke test ──────────────────────────────────────────────
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
echo "  Install dir : $ROOT_DIR  ← this git clone is the app"
echo "  Update      : git pull && ee-game restart"
echo
echo "  Reboot to ensure the WiFi AP comes up cleanly, then connect to:"
echo "    WiFi SSID : $WIFI_SSID"
echo "    Host UI   : http://$BACKEND_AP_HOST:$BACKEND_PORT/host"
echo "    Display   : http://$BACKEND_AP_HOST:$BACKEND_PORT/display"
echo
echo "  Flash an ESP32: ee-game flash"
echo
