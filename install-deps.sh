#!/usr/bin/env bash
# install-deps.sh — Install all system dependencies for EE-Game.
#
# Targets Raspberry Pi OS Bookworm (64-bit). Run once on a fresh system
# before install-pi.sh. Requires internet access and sudo.
#
# Usage: sudo ./install-deps.sh

set -euo pipefail

USERNAME="${SUDO_USER:-${USER}}"

# ── Helpers ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'

info()  { echo -e "${GREEN}✓${NC}  $*"; }
warn()  { echo -e "${YELLOW}!${NC}  $*"; }
error() { echo -e "${RED}✗${NC}  $*" >&2; }
step()  { echo -e "\n${BOLD}── $* ──${NC}"; }

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    echo "Usage: sudo $(basename "$0")"
    echo
    echo "Installs all system dependencies for EE-Game on a blank Raspberry Pi OS"
    echo "Bookworm (64-bit) system: Python 3.13, Node.js 20, WiFi AP tools,"
    echo "PlatformIO, mDNS, and USB serial access for ESP32 flashing."
    exit 0
fi

if [[ "$EUID" -ne 0 ]]; then
    error "Run with sudo: sudo $0"
    exit 1
fi

if [[ ! -f /etc/os-release ]]; then
    error "Cannot detect OS — /etc/os-release not found."
    exit 1
fi

source /etc/os-release
if [[ "${VERSION_CODENAME:-}" != "bookworm" ]]; then
    warn "Targeting Raspberry Pi OS Bookworm. Detected: ${PRETTY_NAME:-unknown}. Continuing anyway."
fi

# ── Core utilities ────────────────────────────────────────────────────────────
step "Core utilities"
apt-get update -qq
apt-get install -y --no-install-recommends \
    git curl wget rsync ca-certificates gnupg lsb-release unzip build-essential

# ── Python 3.13 ───────────────────────────────────────────────────────────────
step "Python 3.13"
if python3.13 --version &>/dev/null 2>&1; then
    info "Already installed: $(python3.13 --version)"
else
    SOURCES_FILE="/etc/apt/sources.list.d/bookworm-backports.list"
    [[ -f "$SOURCES_FILE" ]] || echo "deb http://deb.debian.org/debian bookworm-backports main contrib non-free" > "$SOURCES_FILE"
    apt-get update -qq

    if ! apt-get install -y --no-install-recommends -t bookworm-backports python3.13 python3.13-venv python3.13-dev 2>/dev/null; then
        apt-get install -y --no-install-recommends python3.13 python3.13-venv python3.13-dev || {
            error "Python 3.13 unavailable. Use pyenv: https://github.com/pyenv/pyenv"
            exit 1
        }
    fi
fi

[[ "$(python3 --version 2>&1)" == *"3.13"* ]] || \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 10

python3.13 -m pip --version &>/dev/null 2>&1 || \
    curl -fsSL https://bootstrap.pypa.io/get-pip.py | python3.13

info "$(python3.13 --version) | pip $(python3.13 -m pip --version | cut -d' ' -f2)"

# ── Node.js 20 LTS ────────────────────────────────────────────────────────────
step "Node.js 20 LTS"
if node --version 2>/dev/null | grep -qE '^v(18|19|20|21|22)'; then
    info "Already installed: $(node --version)"
else
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
info "Node $(node --version) | npm $(npm --version)"

# ── WiFi access point ─────────────────────────────────────────────────────────
step "WiFi access point (hostapd + dnsmasq)"
apt-get install -y --no-install-recommends hostapd dnsmasq dhcpcd5
# Leave disabled — install-pi.sh configures and enables them
systemctl unmask hostapd
systemctl disable --now hostapd dnsmasq 2>/dev/null || true
info "Installed (will be activated by install-pi.sh)"

# ── mDNS ─────────────────────────────────────────────────────────────────────
step "mDNS (avahi)"
apt-get install -y --no-install-recommends avahi-daemon libnss-mdns
systemctl enable --now avahi-daemon
info "$(hostname).local is now resolvable on the local network"

# ── USB serial access (ESP32 flashing) ───────────────────────────────────────
step "USB serial access"
if id -nG "$USERNAME" | grep -qw dialout; then
    info "User '$USERNAME' already in dialout group"
else
    usermod -aG dialout "$USERNAME"
    warn "Added '$USERNAME' to dialout — takes effect after logout/reboot"
fi

cat > /etc/udev/rules.d/99-esp32.rules <<'EOF'
# CP210x (common on ESP32-C3 dev boards)
SUBSYSTEM=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"
# CH340/CH341
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", GROUP="dialout"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="55d4", MODE="0666", GROUP="dialout"
# FTDI FT232
SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0666", GROUP="dialout"
EOF
udevadm control --reload-rules && udevadm trigger

# ── PlatformIO ────────────────────────────────────────────────────────────────
step "PlatformIO CLI"
sudo -u "$USERNAME" python3.13 -m pip install --user platformio --break-system-packages
PIO_BIN="$(sudo -u "$USERNAME" python3.13 -m site --user-base)/bin/pio"
if [[ -f "$PIO_BIN" ]]; then
    ln -sf "$PIO_BIN" /usr/local/bin/pio
    info "$(pio --version)"
else
    warn "pio not found at $PIO_BIN — add ~/.local/bin to PATH if needed"
fi

# ── Clean up ──────────────────────────────────────────────────────────────────
apt-get autoremove -y -qq && apt-get clean

# ── Done ──────────────────────────────────────────────────────────────────────
echo
info "All dependencies installed."
echo
echo "  Next: sudo ./install-pi.sh --wifi-ssid \"EE-Game\" --wifi-password \"<passphrase>\""
echo
