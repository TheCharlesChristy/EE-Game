#!/usr/bin/env bash
# install-deps.sh — Install all system dependencies for EE-Game on a fresh
# Raspberry Pi OS (Bookworm, 64-bit) or compatible Debian 12 system.
#
# Run this script once before install-pi.sh. It requires internet access.
# After this script completes, the system has everything needed to build and
# run the backend, frontend, and (optionally) flash ESP32 firmware.
#
# Usage: sudo ./install-deps.sh [OPTIONS]

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
INSTALL_PLATFORMIO=false
INSTALL_WIFI_AP=false
SKIP_NODEJS=false
USERNAME="${SUDO_USER:-${USER}}"

# ── Helpers ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'

info()  { echo -e "${GREEN}[deps]${NC} $*"; }
warn()  { echo -e "${YELLOW}[deps]${NC} $*"; }
error() { echo -e "${RED}[deps]${NC} $*" >&2; }
step()  { echo -e "\n${BOLD}── $* ──${NC}"; }

usage() {
    cat <<EOF
Usage: sudo $(basename "$0") [OPTIONS]

Install all system-level dependencies for EE-Game on a blank Raspberry Pi OS
Bookworm (64-bit) system. Requires internet access and must be run as root
(via sudo).

Options:
      --with-platformio   Also install PlatformIO CLI for flashing ESP32 devices
      --with-wifi-ap      Also install hostapd + dnsmasq for WiFi access point
      --skip-nodejs       Skip Node.js installation (use if already installed)
  -h, --help              Show this help and exit

Examples:
  # Minimum install (backend + frontend only):
  sudo ./install-deps.sh

  # Full install for a classroom deployment (AP + firmware flashing):
  sudo ./install-deps.sh --with-platformio --with-wifi-ap

  # Backend only, no Node.js:
  sudo ./install-deps.sh --skip-nodejs
EOF
}

# ── Argument parsing ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --with-platformio) INSTALL_PLATFORMIO=true; shift ;;
        --with-wifi-ap)    INSTALL_WIFI_AP=true;    shift ;;
        --skip-nodejs)     SKIP_NODEJS=true;        shift ;;
        -h|--help)         usage; exit 0 ;;
        *) error "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ── Root check ────────────────────────────────────────────────────────────────
if [[ "$EUID" -ne 0 ]]; then
    error "This script must be run with sudo."
    error "  sudo $0 $*"
    exit 1
fi

# ── OS check ──────────────────────────────────────────────────────────────────
if [[ ! -f /etc/os-release ]]; then
    error "Cannot detect OS. /etc/os-release not found."
    exit 1
fi

source /etc/os-release
if [[ "${VERSION_CODENAME:-}" != "bookworm" ]]; then
    warn "This script targets Raspberry Pi OS Bookworm."
    warn "Detected: ${PRETTY_NAME:-unknown}. Continuing anyway — some steps may fail."
fi

# ── Step 1: Update package index ──────────────────────────────────────────────
step "Updating package index"
apt-get update -qq

# ── Step 2: Core system utilities ─────────────────────────────────────────────
step "Installing core utilities"
apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    rsync \
    ca-certificates \
    gnupg \
    lsb-release \
    unzip \
    build-essential

# ── Step 3: Python 3.13 ───────────────────────────────────────────────────────
# Bookworm ships Python 3.11. Python 3.13 lives in bookworm-backports.
step "Installing Python 3.13"

if python3.13 --version &>/dev/null 2>&1; then
    info "Python 3.13 already installed: $(python3.13 --version)"
else
    info "Enabling bookworm-backports..."
    SOURCES_FILE="/etc/apt/sources.list.d/bookworm-backports.list"
    if [[ ! -f "$SOURCES_FILE" ]]; then
        echo "deb http://deb.debian.org/debian bookworm-backports main contrib non-free" \
            > "$SOURCES_FILE"
    fi

    apt-get update -qq

    if apt-get install -y --no-install-recommends -t bookworm-backports python3.13 python3.13-venv python3.13-dev 2>/dev/null; then
        info "Python 3.13 installed from backports."
    else
        warn "Backports install failed. Trying default repos..."
        if ! apt-get install -y --no-install-recommends python3.13 python3.13-venv python3.13-dev; then
            error "Python 3.13 is not available via apt on this system."
            error "Build from source or use pyenv: https://github.com/pyenv/pyenv"
            exit 1
        fi
    fi
fi

# Make python3.13 the default python3 if needed
if [[ "$(python3 --version 2>&1)" != *"3.13"* ]]; then
    info "Setting python3.13 as the default python3..."
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 10
fi

# pip for python3.13
if ! python3.13 -m pip --version &>/dev/null 2>&1; then
    info "Installing pip for Python 3.13..."
    curl -fsSL https://bootstrap.pypa.io/get-pip.py | python3.13
fi

info "Python: $(python3.13 --version) | pip: $(python3.13 -m pip --version | cut -d' ' -f2)"

# ── Step 4: Node.js 20 LTS ────────────────────────────────────────────────────
if [[ "$SKIP_NODEJS" == false ]]; then
    step "Installing Node.js 20 LTS"

    if node --version 2>/dev/null | grep -qE '^v(18|19|20|21|22)'; then
        info "Node.js already installed: $(node --version)"
    else
        info "Adding NodeSource repository for Node.js 20 LTS..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
    fi

    info "Node.js: $(node --version) | npm: $(npm --version)"
else
    warn "Skipping Node.js installation (--skip-nodejs)."
fi

# ── Step 5: mDNS — ee-game.local hostname resolution ─────────────────────────
step "Installing mDNS support (avahi)"
apt-get install -y --no-install-recommends \
    avahi-daemon \
    libnss-mdns

# Enable avahi so the Pi is reachable as ee-game.local
systemctl enable avahi-daemon
systemctl start avahi-daemon
info "mDNS enabled. The Pi will be reachable as $(hostname).local"

# ── Step 6: WiFi access point tools (optional) ───────────────────────────────
if [[ "$INSTALL_WIFI_AP" == true ]]; then
    step "Installing WiFi access point tools"
    apt-get install -y --no-install-recommends \
        hostapd \
        dnsmasq \
        dhcpcd5

    # Keep hostapd masked until install-pi.sh --configure-wifi-ap configures it
    systemctl unmask hostapd
    systemctl disable hostapd dnsmasq
    info "hostapd and dnsmasq installed. Run install-pi.sh --configure-wifi-ap to activate."
else
    warn "Skipping WiFi AP tools. Re-run with --with-wifi-ap if needed."
fi

# ── Step 7: USB serial access for ESP32 flashing ─────────────────────────────
step "Configuring USB serial access"

# The dialout group grants access to /dev/ttyUSB* and /dev/ttyACM* without sudo
if id -nG "$USERNAME" | grep -qw dialout; then
    info "User '$USERNAME' is already in the dialout group."
else
    usermod -aG dialout "$USERNAME"
    info "Added '$USERNAME' to the dialout group."
    warn "USB serial access requires a logout/login to take effect."
fi

# Install udev rules for common ESP32 USB chips (CP210x, CH340, FTDI)
UDEV_RULES="/etc/udev/rules.d/99-esp32.rules"
cat > "$UDEV_RULES" <<'EOF'
# CP210x USB to UART (common on ESP32-C3 dev boards)
SUBSYSTEM=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"
# CH340/CH341 USB to UART
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", GROUP="dialout"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="55d4", MODE="0666", GROUP="dialout"
# FTDI FT232
SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0666", GROUP="dialout"
EOF
udevadm control --reload-rules
udevadm trigger
info "udev rules written to $UDEV_RULES"

# ── Step 8: PlatformIO CLI (optional) ────────────────────────────────────────
if [[ "$INSTALL_PLATFORMIO" == true ]]; then
    step "Installing PlatformIO CLI"

    # Install for the invoking user, not root
    sudo -u "$USERNAME" python3.13 -m pip install --user platformio --break-system-packages

    # Symlink into a system path so it's available without modifying PATH
    PIO_BIN="$(sudo -u "$USERNAME" python3.13 -m site --user-base)/bin/pio"
    if [[ -f "$PIO_BIN" ]]; then
        ln -sf "$PIO_BIN" /usr/local/bin/pio
        info "PlatformIO installed: $(pio --version)"
    else
        warn "Could not find pio binary at $PIO_BIN — you may need to add ~/.local/bin to PATH."
    fi
else
    warn "Skipping PlatformIO. Re-run with --with-platformio to install."
    warn "Or install later: pip install platformio"
fi

# ── Step 9: Clean up ─────────────────────────────────────────────────────────
step "Cleaning up"
apt-get autoremove -y -qq
apt-get clean

# ── Summary ───────────────────────────────────────────────────────────────────
echo
info "All dependencies installed."
echo
echo "  Python  : $(python3.13 --version)"
if [[ "$SKIP_NODEJS" == false ]]; then
    echo "  Node.js : $(node --version)"
    echo "  npm     : $(npm --version)"
fi
[[ "$INSTALL_PLATFORMIO" == true ]] && echo "  pio     : $(pio --version 2>/dev/null || echo 'see PATH note above')"
echo
echo "Next steps:"
echo "  1. Run the application installer:"
echo "       ./install-pi.sh"
echo "     Or for a full classroom deployment:"
echo "       ./install-pi.sh --prod --wifi-ssid \"EE-Game\" --wifi-password \"<passphrase>\""
echo
if [[ "$INSTALL_PLATFORMIO" == true ]]; then
    echo "  2. Flash an ESP32 device:"
    echo "       ./flash-device.sh"
    echo
fi
if id -nG "$USERNAME" | grep -qw dialout && [[ "$INSTALL_PLATFORMIO" == true ]]; then
    warn "Log out and back in (or reboot) for dialout group membership to take effect."
fi
