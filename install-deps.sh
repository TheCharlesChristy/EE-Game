#!/usr/bin/env bash
# install-deps.sh — Install all system dependencies for EE-Game.
#
# Supports Debian-based systems (apt) and RPM-based systems (dnf/yum).
# Detects the package manager automatically. Installs the latest available
# Python 3.12+, Node.js LTS, WiFi AP tools, PlatformIO, mDNS, and USB serial
# access for ESP32 flashing.
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
    cat <<EOF
Usage: sudo $(basename "$0")

Installs all system dependencies for EE-Game: Python 3.12+ (latest available),
Node.js LTS, WiFi AP tools (hostapd, dnsmasq), PlatformIO, mDNS, and USB serial
access for ESP32 flashing.

Supports Debian-based (apt) and RPM-based (dnf/yum) distributions.
EOF
    exit 0
fi

[[ "$EUID" -eq 0 ]] || { error "Run with sudo: sudo $0"; exit 1; }
[[ -f /etc/os-release ]] || { error "Cannot detect OS — /etc/os-release not found."; exit 1; }
source /etc/os-release

# ── Detect package manager ────────────────────────────────────────────────────
step "Detecting package manager"
if command -v apt-get &>/dev/null; then
    PKG_MANAGER="apt"
    info "Debian-based system: ${PRETTY_NAME:-unknown}"
elif command -v dnf &>/dev/null; then
    PKG_MANAGER="dnf"
    info "RPM-based system (dnf): ${PRETTY_NAME:-unknown}"
elif command -v yum &>/dev/null; then
    PKG_MANAGER="yum"
    info "RPM-based system (yum): ${PRETTY_NAME:-unknown}"
else
    error "No supported package manager found (need apt, dnf, or yum)."
    exit 1
fi

pkg_install() {
    case "$PKG_MANAGER" in
        apt)     apt-get install -y --no-install-recommends "$@" ;;
        dnf|yum) "$PKG_MANAGER" install -y "$@" ;;
    esac
}

pkg_update() {
    case "$PKG_MANAGER" in
        apt)     apt-get update -qq ;;
        dnf|yum) "$PKG_MANAGER" makecache -q ;;
    esac
}

# ── Core utilities ────────────────────────────────────────────────────────────
step "Core utilities"
pkg_update
case "$PKG_MANAGER" in
    apt)     pkg_install git curl wget ca-certificates gnupg lsb-release unzip build-essential ;;
    dnf|yum) pkg_install git curl wget ca-certificates gnupg2 unzip make gcc gcc-c++ ;;
esac
info "Core utilities ready"

# ── Python 3.12+ (latest available) ──────────────────────────────────────────
step "Python 3.12+ (latest available)"

# Candidates from newest to oldest — extend this list as new releases ship.
PYTHON_CANDIDATES=(3.15 3.14 3.13 3.12)

# Check for a usable version already installed.
PYTHON_BIN=""
for ver in "${PYTHON_CANDIDATES[@]}"; do
    if command -v "python${ver}" &>/dev/null; then
        PYTHON_BIN="python${ver}"
        info "Already installed: $("${PYTHON_BIN}" --version)"
        break
    fi
done

if [[ -z "$PYTHON_BIN" ]]; then
    case "$PKG_MANAGER" in
        apt)
            # Pass 1: try installing each candidate from the default apt repos.
            for ver in "${PYTHON_CANDIDATES[@]}"; do
                if apt-get install -y --no-install-recommends \
                       "python${ver}" "python${ver}-venv" "python${ver}-dev" &>/dev/null; then
                    PYTHON_BIN="python${ver}"
                    break
                fi
            done

            # Pass 2 (Debian only): try backports.
            if [[ -z "$PYTHON_BIN" ]] && \
               { [[ "${ID:-}" == "debian" ]] || [[ "${ID_LIKE:-}" == *"debian"* && "${ID:-}" != "ubuntu" ]]; }; then
                CODENAME="${VERSION_CODENAME:-bookworm}"
                SOURCES_FILE="/etc/apt/sources.list.d/${CODENAME}-backports.list"
                [[ -f "$SOURCES_FILE" ]] || \
                    echo "deb http://deb.debian.org/debian ${CODENAME}-backports main contrib non-free" \
                         > "$SOURCES_FILE"
                apt-get update -qq
                for ver in "${PYTHON_CANDIDATES[@]}"; do
                    if apt-get install -y --no-install-recommends \
                           -t "${CODENAME}-backports" \
                           "python${ver}" "python${ver}-venv" "python${ver}-dev" &>/dev/null; then
                        PYTHON_BIN="python${ver}"
                        break
                    fi
                done
            fi

            # Pass 3 (Ubuntu only): try the deadsnakes PPA.
            if [[ -z "$PYTHON_BIN" ]] && \
               { [[ "${ID:-}" == "ubuntu" ]] || [[ "${ID_LIKE:-}" == *"ubuntu"* ]]; }; then
                pkg_install software-properties-common
                add-apt-repository -y ppa:deadsnakes/ppa
                apt-get update -qq
                for ver in "${PYTHON_CANDIDATES[@]}"; do
                    if apt-get install -y --no-install-recommends \
                           "python${ver}" "python${ver}-venv" "python${ver}-dev" &>/dev/null; then
                        PYTHON_BIN="python${ver}"
                        break
                    fi
                done
            fi
            ;;

        dnf|yum)
            # Try versioned packages (available on Fedora 37+, RHEL 9+ with EPEL).
            for ver in "${PYTHON_CANDIDATES[@]}"; do
                if "$PKG_MANAGER" install -y "python${ver}" "python${ver}-devel" &>/dev/null; then
                    PYTHON_BIN="python${ver}"
                    break
                fi
            done

            # Fall back to the system python3 if it's already >= 3.12.
            if [[ -z "$PYTHON_BIN" ]]; then
                pkg_install python3 python3-devel python3-pip
                if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; then
                    PYTHON_BIN="python3"
                fi
            fi
            ;;
    esac

    if [[ -z "$PYTHON_BIN" ]]; then
        error "Could not install Python 3.12+ from any known source."
        error "Install manually via pyenv: https://github.com/pyenv/pyenv"
        exit 1
    fi
    info "Installed: $("${PYTHON_BIN}" --version)"
fi

# Register with update-alternatives so 'python3' resolves to our version.
if [[ "$PYTHON_BIN" != "python3" ]] && command -v update-alternatives &>/dev/null; then
    PY_PATH="$(command -v "${PYTHON_BIN}")"
    update-alternatives --install /usr/bin/python3 python3 "$PY_PATH" 10 2>/dev/null || true
fi

# Ensure pip is present.
"${PYTHON_BIN}" -m pip --version &>/dev/null || \
    curl -fsSL https://bootstrap.pypa.io/get-pip.py | "${PYTHON_BIN}"

info "$("${PYTHON_BIN}" --version) | pip $("${PYTHON_BIN}" -m pip --version | cut -d' ' -f2)"

# ── Node.js LTS ───────────────────────────────────────────────────────────────
step "Node.js LTS"
NODE_MAJOR="$(node --version 2>/dev/null | grep -oE '^v[0-9]+' | tr -d 'v' || echo 0)"
if [[ "$NODE_MAJOR" -ge 20 ]]; then
    info "Already installed: $(node --version)"
else
    case "$PKG_MANAGER" in
        apt)     curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - ;;
        dnf|yum) curl -fsSL https://rpm.nodesource.com/setup_lts.x | bash - ;;
    esac
    pkg_install nodejs
fi
info "Node $(node --version) | npm $(npm --version)"

# ── WiFi access point ─────────────────────────────────────────────────────────
step "WiFi access point (hostapd + dnsmasq)"
case "$PKG_MANAGER" in
    apt)     pkg_install hostapd dnsmasq dhcpcd5 ;;
    dnf|yum) pkg_install hostapd dnsmasq ;;
esac
# Leave disabled — install-pi.sh configures and enables them.
systemctl unmask hostapd
systemctl disable --now hostapd dnsmasq 2>/dev/null || true
info "Installed (will be activated by install-pi.sh)"

# ── mDNS ─────────────────────────────────────────────────────────────────────
step "mDNS"
case "$PKG_MANAGER" in
    apt)     pkg_install avahi-daemon libnss-mdns ;;
    dnf|yum) pkg_install avahi nss-mdns ;;
esac
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
info "udev rules written, dialout group configured"

# ── PlatformIO ────────────────────────────────────────────────────────────────
step "PlatformIO CLI"
# --break-system-packages is required on PEP 668 systems (Debian 12+, Ubuntu 23+);
# older systems don't recognise the flag, so we fall back without it.
sudo -u "$USERNAME" "${PYTHON_BIN}" -m pip install --user platformio --break-system-packages 2>/dev/null || \
    sudo -u "$USERNAME" "${PYTHON_BIN}" -m pip install --user platformio
PIO_BIN="$(sudo -u "$USERNAME" "${PYTHON_BIN}" -m site --user-base)/bin/pio"
if [[ -f "$PIO_BIN" ]]; then
    ln -sf "$PIO_BIN" /usr/local/bin/pio
    info "$(pio --version)"
else
    warn "pio not found at $PIO_BIN — add ~/.local/bin to PATH if needed"
fi

# ── Clean up ──────────────────────────────────────────────────────────────────
case "$PKG_MANAGER" in
    apt)     apt-get autoremove -y -qq && apt-get clean ;;
    dnf|yum) "$PKG_MANAGER" autoremove -y -q 2>/dev/null || true ;;
esac

# ── Done ──────────────────────────────────────────────────────────────────────
echo
info "All dependencies installed."
echo
echo "  Next: edit .env, then run: sudo ./install-pi.sh"
echo
