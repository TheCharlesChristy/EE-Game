#!/usr/bin/env bash
# flash-device.sh — Build and flash EE-Game firmware onto an ESP32 device.
#
# Requires PlatformIO CLI (https://docs.platformio.org/en/latest/core/installation/).
# Install with: pip install platformio
#
# Usage: ./flash-device.sh [OPTIONS]

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
TARGET="esp32-c3"
SERIAL_PORT=""
MONITOR=false
BUILD_ONLY=false
BAUD=115200

# ── Helpers ───────────────────────────────────────────────────────────────────
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

info()  { echo -e "${GREEN}[flash]${NC} $*"; }
warn()  { echo -e "${YELLOW}[flash]${NC} $*"; }
error() { echo -e "${RED}[flash]${NC} $*" >&2; }

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Build and flash EE-Game firmware onto a connected ESP32 device.
Run from any directory — the script locates the firmware/ folder automatically.

Options:
  -t, --target TARGET    PlatformIO environment to build     (default: esp32-c3)
                         Supported: esp32-c3, esp32dev
  -p, --port PORT        Serial port of the device           (default: auto-detect)
                         Examples: /dev/ttyUSB0, /dev/ttyACM0, COM3
  -m, --monitor          Open serial monitor after flashing
  -b, --baud RATE        Baud rate for serial monitor        (default: 115200)
      --build-only       Build firmware without flashing
  -h, --help             Show this help and exit

Examples:
  # Flash to an auto-detected ESP32-C3:
  ./flash-device.sh

  # Flash to a specific serial port:
  ./flash-device.sh --port /dev/ttyUSB0

  # Flash the esp32dev variant and open the serial monitor:
  ./flash-device.sh --target esp32dev --monitor

  # Build only (no device needed):
  ./flash-device.sh --build-only

  # Flash and monitor at a different baud rate:
  ./flash-device.sh --port /dev/ttyACM0 --monitor --baud 9600
EOF
}

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--target)     TARGET="$2";      shift 2 ;;
        -p|--port)       SERIAL_PORT="$2"; shift 2 ;;
        -m|--monitor)    MONITOR=true;     shift   ;;
        -b|--baud)       BAUD="$2";        shift 2 ;;
           --build-only) BUILD_ONLY=true;  shift   ;;
        -h|--help)       usage; exit 0 ;;
        *) error "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# ── Preflight checks ──────────────────────────────────────────────────────────
FIRMWARE_DIR="$ROOT_DIR/firmware"

if [[ ! -f "$FIRMWARE_DIR/platformio.ini" ]]; then
    error "firmware/platformio.ini not found. Run this script from the repository root."
    exit 1
fi

if ! command -v pio &>/dev/null; then
    error "PlatformIO CLI (pio) not found."
    error "Install it with: pip install platformio"
    error "Or see: https://docs.platformio.org/en/latest/core/installation/"
    exit 1
fi

# Validate target
VALID_TARGETS=("esp32-c3" "esp32dev")
if [[ ! " ${VALID_TARGETS[*]} " =~ " ${TARGET} " ]]; then
    error "Unknown target: '$TARGET'. Valid targets: ${VALID_TARGETS[*]}"
    exit 1
fi

# ── Build ─────────────────────────────────────────────────────────────────────
info "Building firmware for target: $TARGET"
cd "$FIRMWARE_DIR"
pio run -e "$TARGET"
info "Build complete."

# ── Flash ─────────────────────────────────────────────────────────────────────
if [[ "$BUILD_ONLY" == false ]]; then
    UPLOAD_ARGS=(-e "$TARGET" --target upload)

    if [[ -n "$SERIAL_PORT" ]]; then
        info "Flashing to $SERIAL_PORT..."
        UPLOAD_ARGS+=(--upload-port "$SERIAL_PORT")
    else
        info "Flashing (auto-detecting port)..."
        warn "If upload fails, specify the port with --port /dev/ttyUSB0"
    fi

    pio run "${UPLOAD_ARGS[@]}"
    info "Flash complete."
else
    warn "Skipping flash (--build-only). Binary at: .pio/build/$TARGET/firmware.bin"
fi

# ── Monitor ───────────────────────────────────────────────────────────────────
if [[ "$MONITOR" == true ]]; then
    info "Opening serial monitor (baud: $BAUD). Press Ctrl+C to exit."
    MONITOR_ARGS=(device monitor --baud "$BAUD")
    if [[ -n "$SERIAL_PORT" ]]; then
        MONITOR_ARGS+=(--port "$SERIAL_PORT")
    fi
    pio "${MONITOR_ARGS[@]}"
fi
