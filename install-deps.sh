#!/usr/bin/env bash
# install-deps.sh — Install all system dependencies for EE-Game.
#
# Uses only the distribution's own package manager (apt or dnf/yum).
# If a package cannot be installed it is skipped and reported at the end
# so you can install it manually before running install-pi.sh.
#
# Usage: sudo ./install-deps.sh

set -uo pipefail

USERNAME="${SUDO_USER:-${USER}}"
MISSING=()   # Populated by try_install; reported at the end.

# ── Helpers ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
info()  { echo -e "${GREEN}✓${NC}  $*"; }
warn()  { echo -e "${YELLOW}!${NC}  $*"; }
error() { echo -e "${RED}✗${NC}  $*" >&2; }
step()  { echo -e "\n${BOLD}── $* ──${NC}"; }

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    cat <<EOF
Usage: sudo $(basename "$0")

Installs EE-Game system dependencies using only the distribution's own package
manager. Packages that cannot be found are skipped and listed at the end.

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

pkg_update() {
    case "$PKG_MANAGER" in
        apt)     apt-get update -qq ;;
        dnf|yum) "$PKG_MANAGER" makecache -q ;;
    esac
}

# Install packages, silently skipping those that are unavailable.
# Usage: try_install "Human label" pkg1 pkg2 ...
try_install() {
    local label="$1"; shift
    local failed=()
    for pkg in "$@"; do
        case "$PKG_MANAGER" in
            apt)
                if ! apt-get install -y --no-install-recommends "$pkg" &>/dev/null; then
                    failed+=("$pkg")
                fi
                ;;
            dnf|yum)
                if ! "$PKG_MANAGER" install -y "$pkg" &>/dev/null; then
                    failed+=("$pkg")
                fi
                ;;
        esac
    done
    if [[ ${#failed[@]} -gt 0 ]]; then
        warn "Could not install: ${failed[*]}  (skipping)"
        MISSING+=("$label: ${failed[*]}")
        return 1
    fi
    return 0
}

# ── Core utilities ────────────────────────────────────────────────────────────
step "Core utilities"
pkg_update
case "$PKG_MANAGER" in
    apt)     try_install "core utilities" git curl wget ca-certificates gnupg lsb-release unzip build-essential ;;
    dnf|yum) try_install "core utilities" git curl wget ca-certificates gnupg2 unzip make gcc gcc-c++ ;;
esac
info "Core utilities done"

# ── Python 3.12+ ──────────────────────────────────────────────────────────────
step "Python 3.12+"

# Try candidate versions newest-first; all are standard distro packages on
# modern systems (Ubuntu 24.04, Fedora 40+, Debian 12 backports, etc.).
PYTHON_BIN=""
for ver in 3.15 3.14 3.13 3.12; do
    if command -v "python${ver}" &>/dev/null; then
        PYTHON_BIN="python${ver}"
        info "Already installed: $("${PYTHON_BIN}" --version)"
        break
    fi
    case "$PKG_MANAGER" in
        apt)
            if apt-get install -y --no-install-recommends \
                   "python${ver}" "python${ver}-venv" "python${ver}-dev" &>/dev/null; then
                PYTHON_BIN="python${ver}"
            fi
            ;;
        dnf|yum)
            if "$PKG_MANAGER" install -y "python${ver}" "python${ver}-devel" &>/dev/null; then
                PYTHON_BIN="python${ver}"
            fi
            ;;
    esac
    [[ -n "$PYTHON_BIN" ]] && { info "Installed: $("${PYTHON_BIN}" --version)"; break; }
done

if [[ -z "$PYTHON_BIN" ]]; then
    # No versioned package found; try the generic python3 and accept it if >= 3.12.
    case "$PKG_MANAGER" in
        apt)     apt-get install -y --no-install-recommends python3 python3-venv python3-dev &>/dev/null || true ;;
        dnf|yum) "$PKG_MANAGER" install -y python3 python3-devel python3-pip &>/dev/null || true ;;
    esac
    if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; then
        PYTHON_BIN="python3"
        info "Using system python3: $(python3 --version)"
    else
        SYS_VER="$(python3 --version 2>/dev/null || echo 'not found')"
        warn "System python3 is ${SYS_VER} — need 3.12+; install manually"
        MISSING+=("python3.12+ (system has ${SYS_VER})")
        PYTHON_BIN="python3"   # Best effort; install-pi.sh will check again.
    fi
fi

# Register with update-alternatives so 'python3' points at the chosen version.
if [[ "$PYTHON_BIN" != "python3" ]] && command -v update-alternatives &>/dev/null; then
    PY_PATH="$(command -v "${PYTHON_BIN}")"
    update-alternatives --install /usr/bin/python3 python3 "$PY_PATH" 10 2>/dev/null || true
fi

# ── Node.js ───────────────────────────────────────────────────────────────────
step "Node.js"
NODE_MAJOR="$(node --version 2>/dev/null | grep -oE '^v[0-9]+' | tr -d 'v' || echo 0)"
if [[ "$NODE_MAJOR" -ge 18 ]]; then
    info "Already installed: $(node --version)"
else
    case "$PKG_MANAGER" in
        apt)     try_install "nodejs" nodejs npm ;;
        dnf|yum) try_install "nodejs" nodejs npm ;;
    esac
    NODE_MAJOR="$(node --version 2>/dev/null | grep -oE '^v[0-9]+' | tr -d 'v' || echo 0)"
    if [[ "$NODE_MAJOR" -lt 18 ]]; then
        warn "Installed Node.js v${NODE_MAJOR} is below the required v18 — install a newer version manually"
        MISSING+=("nodejs >= 18 (system has v${NODE_MAJOR})")
    else
        info "Node $(node --version) | npm $(npm --version)"
    fi
fi

# ── WiFi access point ─────────────────────────────────────────────────────────
step "WiFi access point (hostapd + dnsmasq)"
case "$PKG_MANAGER" in
    apt)     try_install "hostapd/dnsmasq" hostapd dnsmasq dhcpcd5 ;;
    dnf|yum) try_install "hostapd/dnsmasq" hostapd dnsmasq ;;
esac
# Leave disabled — install-pi.sh configures and enables them.
systemctl unmask hostapd 2>/dev/null || true
systemctl disable --now hostapd dnsmasq 2>/dev/null || true
info "WiFi AP packages done (will be activated by install-pi.sh)"

# ── mDNS ─────────────────────────────────────────────────────────────────────
step "mDNS"
case "$PKG_MANAGER" in
    apt)     try_install "avahi/mDNS" avahi-daemon libnss-mdns ;;
    dnf|yum) try_install "avahi/mDNS" avahi nss-mdns ;;
esac
systemctl enable --now avahi-daemon 2>/dev/null || true
info "$(hostname).local should be resolvable on the local network"

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

# ── PlatformIO (via pip) ──────────────────────────────────────────────────────
step "PlatformIO CLI"
if command -v pio &>/dev/null; then
    info "Already installed: $(pio --version)"
else
    PIO_INSTALLED=false
    if command -v "${PYTHON_BIN}" &>/dev/null; then
        if sudo -u "$USERNAME" "${PYTHON_BIN}" -m pip install --user platformio \
               --break-system-packages &>/dev/null 2>&1 || \
           sudo -u "$USERNAME" "${PYTHON_BIN}" -m pip install --user platformio &>/dev/null; then
            PIO_BIN="$(sudo -u "$USERNAME" "${PYTHON_BIN}" -m site --user-base)/bin/pio"
            if [[ -f "$PIO_BIN" ]]; then
                ln -sf "$PIO_BIN" /usr/local/bin/pio
                info "$(pio --version)"
                PIO_INSTALLED=true
            fi
        fi
    fi
    if [[ "$PIO_INSTALLED" == false ]]; then
        warn "Could not install PlatformIO — install manually: pip install platformio"
        MISSING+=("platformio (pip install platformio)")
    fi
fi

# ── Clean up ──────────────────────────────────────────────────────────────────
case "$PKG_MANAGER" in
    apt)     apt-get autoremove -y -qq && apt-get clean ;;
    dnf|yum) "$PKG_MANAGER" autoremove -y -q 2>/dev/null || true ;;
esac

# ── Summary ───────────────────────────────────────────────────────────────────
echo
if [[ ${#MISSING[@]} -eq 0 ]]; then
    info "All dependencies installed successfully."
else
    warn "The following could not be installed automatically:"
    for item in "${MISSING[@]}"; do
        echo "    •  $item"
    done
    echo
    echo "  Install these manually, then run: sudo ./install-pi.sh"
fi
echo
echo "  Next: edit .env, then run: sudo ./install-pi.sh"
echo
