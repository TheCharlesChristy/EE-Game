#!/usr/bin/env bash
# install-pi.sh — Install EE-Game onto a Raspberry Pi.
#
# Run this script on the Pi itself (or via SSH) from inside the cloned
# repository. It creates the system user, copies files, sets up the Python
# virtual environment, builds the frontend, and installs the systemd service.
#
# Usage: ./install-pi.sh [OPTIONS]
#
# The script is idempotent — re-running it updates an existing installation
# without losing the database or .env file.

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────
INSTALL_DIR="/opt/ee-game"
SERVICE_USER="ee-game"
PORT=8000
BUILD_FRONTEND=true
CONFIGURE_WIFI_AP=false
WIFI_SSID="ee-game"
WIFI_CHANNEL=7
DRY_RUN=false
SKIP_DEPS=false

# ── Helpers ──────────────────────────────────────────────────────────────────
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

info()    { echo -e "${GREEN}[install]${NC} $*"; }
warn()    { echo -e "${YELLOW}[install]${NC} $*"; }
error()   { echo -e "${RED}[install]${NC} $*" >&2; }
run()     { if [[ "$DRY_RUN" == true ]]; then echo "[dry-run] $*"; else "$@"; fi; }
run_sudo(){ if [[ "$DRY_RUN" == true ]]; then echo "[dry-run] sudo $*"; else sudo "$@"; fi; }

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Install EE-Game onto this Raspberry Pi. Run as a normal user with sudo access
from inside the cloned repository.

Options:
  -d, --install-dir DIR     Destination directory            (default: /opt/ee-game)
  -u, --user USER           System user to run the service   (default: ee-game)
  -p, --port PORT           Backend HTTP port                (default: 8000)
      --no-frontend-build   Skip 'npm run build' (use if dist/ already exists)
      --configure-wifi-ap   Set up hostapd + dnsmasq access point on wlan0
      --wifi-ssid SSID      WiFi network name for AP mode    (default: ee-game)
      --wifi-channel N      WiFi channel for AP mode         (default: 7)
      --skip-deps           Skip pip install (use if venv is already up to date)
      --dry-run             Print actions without executing them
  -h, --help                Show this help and exit

Examples:
  # Standard first-time install:
  ./install-pi.sh

  # Custom install dir and port:
  ./install-pi.sh --install-dir /home/pi/ee-game --port 9000

  # Update an existing install without rebuilding the frontend:
  ./install-pi.sh --no-frontend-build --skip-deps

  # Full classroom setup including WiFi access point:
  ./install-pi.sh --configure-wifi-ap --wifi-ssid "EE-Game" --wifi-channel 6
EOF
}

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--install-dir)      INSTALL_DIR="$2";       shift 2 ;;
        -u|--user)             SERVICE_USER="$2";      shift 2 ;;
        -p|--port)             PORT="$2";              shift 2 ;;
           --no-frontend-build) BUILD_FRONTEND=false;  shift   ;;
           --configure-wifi-ap) CONFIGURE_WIFI_AP=true; shift  ;;
           --wifi-ssid)        WIFI_SSID="$2";         shift 2 ;;
           --wifi-channel)     WIFI_CHANNEL="$2";      shift 2 ;;
           --skip-deps)        SKIP_DEPS=true;         shift   ;;
           --dry-run)          DRY_RUN=true;            shift   ;;
        -h|--help)             usage; exit 0 ;;
        *) error "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ── Preflight checks ──────────────────────────────────────────────────────────
if [[ ! -f "$ROOT_DIR/host/backend/pyproject.toml" ]]; then
    error "Run this script from the root of the EE-Game repository."
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    error "python3 not found. Install Python 3.12+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info[:2] >= (3,12))')
if [[ "$PYTHON_VERSION" != "True" ]]; then
    error "Python 3.12 or later is required. Found: $(python3 --version)"
    exit 1
fi

if [[ "$BUILD_FRONTEND" == true ]] && ! command -v npm &>/dev/null; then
    error "npm not found. Install Node.js 18+ or use --no-frontend-build."
    exit 1
fi

# ── Step 1: Build frontend ────────────────────────────────────────────────────
if [[ "$BUILD_FRONTEND" == true ]]; then
    info "Building React frontend..."
    run bash -c "cd '$ROOT_DIR/host/frontend' && npm install && npm run build"
    info "Frontend built → host/frontend/dist/"
else
    warn "Skipping frontend build (--no-frontend-build)."
    if [[ ! -d "$ROOT_DIR/host/frontend/dist" ]]; then
        error "host/frontend/dist/ does not exist. Run without --no-frontend-build first."
        exit 1
    fi
fi

# ── Step 2: Create system user ────────────────────────────────────────────────
info "Creating system user '$SERVICE_USER'..."
if id "$SERVICE_USER" &>/dev/null; then
    warn "User '$SERVICE_USER' already exists — skipping."
else
    run_sudo useradd --system --shell /bin/false --home "$INSTALL_DIR" "$SERVICE_USER"
fi

# ── Step 3: Copy application files ───────────────────────────────────────────
info "Copying files to $INSTALL_DIR..."
run_sudo mkdir -p "$INSTALL_DIR"
run_sudo rsync -a --delete \
    --exclude='.git/' \
    --exclude='host/backend/.venv/' \
    --exclude='host/backend/data/' \
    --exclude='host/backend/.env' \
    --exclude='host/frontend/node_modules/' \
    --exclude='firmware/.pio/' \
    "$ROOT_DIR/" "$INSTALL_DIR/"
run_sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# ── Step 4: Python virtual environment ───────────────────────────────────────
VENV="$INSTALL_DIR/host/backend/.venv"
info "Setting up Python virtual environment..."
if [[ ! -d "$VENV" ]]; then
    run_sudo -u "$SERVICE_USER" python3 -m venv "$VENV"
fi

if [[ "$SKIP_DEPS" == false ]]; then
    info "Installing Python dependencies..."
    run_sudo -u "$SERVICE_USER" "$VENV/bin/pip" install --quiet -e "$INSTALL_DIR/host/backend"
else
    warn "Skipping pip install (--skip-deps)."
fi

# ── Step 5: Database directory ────────────────────────────────────────────────
info "Ensuring data directory exists..."
run_sudo -u "$SERVICE_USER" mkdir -p "$INSTALL_DIR/host/backend/data"

# ── Step 6: Environment file ──────────────────────────────────────────────────
ENV_FILE="$INSTALL_DIR/host/backend/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    info "Creating .env from template..."
    run_sudo -u "$SERVICE_USER" bash -c "cat > '$ENV_FILE'" <<EOF
BACKEND_HOST=0.0.0.0
BACKEND_PORT=$PORT
LOG_LEVEL=INFO
HEARTBEAT_TIMEOUT_SECONDS=30
STATIC_FILES_DIR=../../frontend/dist
EOF
    run_sudo chmod 600 "$ENV_FILE"
else
    warn ".env already exists — not overwritten. Edit $ENV_FILE to change settings."
fi

# ── Step 7: systemd service ───────────────────────────────────────────────────
info "Installing systemd service..."
SERVICE_SRC="$INSTALL_DIR/docs/deployment/ee-game.service"
SERVICE_DST="/etc/systemd/system/ee-game.service"

# Patch the port in the service ExecStart line
run_sudo bash -c "
    sed 's|--port [0-9]*|--port $PORT|g' '$SERVICE_SRC' > '$SERVICE_DST'
"
run_sudo systemctl daemon-reload
run_sudo systemctl enable ee-game.service

# ── Step 8: WiFi access point (optional) ─────────────────────────────────────
if [[ "$CONFIGURE_WIFI_AP" == true ]]; then
    info "Configuring WiFi access point (SSID: $WIFI_SSID, channel: $WIFI_CHANNEL)..."

    if ! command -v hostapd &>/dev/null || ! command -v dnsmasq &>/dev/null; then
        error "hostapd and dnsmasq are required for --configure-wifi-ap."
        error "Install with: sudo apt-get install hostapd dnsmasq"
        exit 1
    fi

    HOSTAPD_CONF=$(cat <<EOF
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
wpa_passphrase=changeme123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF
)
    run_sudo bash -c "echo '$HOSTAPD_CONF' > /etc/hostapd/hostapd.conf"
    run_sudo bash -c "echo 'DAEMON_CONF=\"/etc/hostapd/hostapd.conf\"' >> /etc/default/hostapd"

    DNSMASQ_CONF="interface=wlan0
dhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,24h"
    run_sudo bash -c "echo '$DNSMASQ_CONF' >> /etc/dnsmasq.conf"

    # Static IP on wlan0
    run_sudo bash -c "echo -e '\ninterface wlan0\nstatic ip_address=192.168.4.1/24\nnohook wpa_supplicant' >> /etc/dhcpcd.conf"

    run_sudo systemctl unmask hostapd
    run_sudo systemctl enable hostapd dnsmasq

    warn "WiFi AP configured. Change the passphrase in /etc/hostapd/hostapd.conf before use."
    warn "Reboot the Pi for the access point to become active."
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo
info "Installation complete."
echo
echo "  Install directory : $INSTALL_DIR"
echo "  Service user      : $SERVICE_USER"
echo "  Port              : $PORT"
echo
echo "  Start the service :"
echo "    sudo systemctl start ee-game"
echo
echo "  View logs         :"
echo "    sudo journalctl -u ee-game -f"
echo
echo "  Health check      :"
echo "    curl http://localhost:$PORT/health"
echo
if [[ "$CONFIGURE_WIFI_AP" == true ]]; then
    echo "  After reboot, devices and browsers connect to:"
    echo "    WiFi SSID : $WIFI_SSID"
    echo "    Host URL  : http://192.168.4.1:$PORT/host"
    echo "    Display   : http://192.168.4.1:$PORT/display"
    echo
fi
