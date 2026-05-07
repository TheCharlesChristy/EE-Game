#!/usr/bin/env bash
# flash-device.sh — Build and flash EE-Game firmware onto an ESP32 device.
#
# Reads WiFi credentials and backend address from .env in the repo root
# (or host/backend/.env if that exists) and bakes them into the firmware.
#
# Usage: ./flash-device.sh [OPTIONS]

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIRMWARE_DIR="$ROOT_DIR/firmware"

TARGET="esp32-c3"
SERIAL_PORT=""
MONITOR=false
BUILD_ONLY=false
BAUD=115200

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[flash]${NC} $*"; }
warn()  { echo -e "${YELLOW}[flash]${NC} $*"; }
error() { echo -e "${RED}[flash]${NC} $*" >&2; }

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Build and flash EE-Game firmware. WiFi credentials are read automatically from
.env — no arguments needed for credentials.

Options:
  -t, --target TARGET    PlatformIO environment  (default: esp32-c3)
                         Supported: esp32-c3, esp32dev
  -p, --port PORT        Serial port             (default: auto-detect)
  -m, --monitor          Open serial monitor after flashing
  -b, --baud RATE        Monitor baud rate       (default: 115200)
      --build-only       Build without flashing
  -h, --help             Show this help

Examples:
  ./flash-device.sh
  ./flash-device.sh --port /dev/ttyUSB0
  ./flash-device.sh --target esp32dev --monitor
  ./flash-device.sh --build-only
EOF
}

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

# ── Preflight ─────────────────────────────────────────────────────────────────
[[ -f "$FIRMWARE_DIR/platformio.ini" ]] || {
    error "firmware/platformio.ini not found. Run from the repository root."
    exit 1
}

command -v pio &>/dev/null || {
    error "PlatformIO CLI (pio) not found. Install: pip install platformio"
    exit 1
}

VALID_TARGETS=("esp32-c3" "esp32dev")
if [[ ! " ${VALID_TARGETS[*]} " =~ " ${TARGET} " ]]; then
    error "Unknown target: '$TARGET'. Valid: ${VALID_TARGETS[*]}"
    exit 1
fi

# ── Load .env (credentials must come from here, not be hardcoded) ─────────────
# Prefer the live backend .env; fall back to the root template.
if [[ -f "$ROOT_DIR/host/backend/.env" ]]; then
    ENV_FILE="$ROOT_DIR/host/backend/.env"
elif [[ -f "$ROOT_DIR/.env" ]]; then
    ENV_FILE="$ROOT_DIR/.env"
else
    error "No .env file found. Copy the root .env template and fill in credentials."
    exit 1
fi

env_get() {
    local key="$1" default="${2:-}"
    local val
    val=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)
    echo "${val:-$default}"
}

WIFI_SSID=$(env_get "WIFI_SSID" "")
WIFI_PASSWORD=$(env_get "WIFI_PASSWORD" "")
BACKEND_HOST=$(env_get "BACKEND_AP_HOST" "192.168.4.1")
BACKEND_PORT=$(env_get "BACKEND_PORT" "8000")

[[ -n "$WIFI_SSID" ]]     || { error "WIFI_SSID not set in $ENV_FILE"; exit 1; }
[[ -n "$WIFI_PASSWORD" ]] || { error "WIFI_PASSWORD not set in $ENV_FILE"; exit 1; }

info "Target      : $TARGET"
info "WiFi SSID   : $WIFI_SSID"
info "Backend     : $BACKEND_HOST:$BACKEND_PORT"
info "Config from : $ENV_FILE"
echo

BUILD_FLAGS="-D WIFI_SSID='\"${WIFI_SSID}\"'"
BUILD_FLAGS+=" -D WIFI_PASSWORD='\"${WIFI_PASSWORD}\"'"
BUILD_FLAGS+=" -D BACKEND_HOST='\"${BACKEND_HOST}\"'"
BUILD_FLAGS+=" -D BACKEND_PORT=${BACKEND_PORT}"

# ── Build ─────────────────────────────────────────────────────────────────────
cd "$FIRMWARE_DIR"

# Always clean before building — PlatformIO caches compiled objects and won't
# recompile when only PLATFORMIO_BUILD_FLAGS (env vars) change. Without this,
# a changed SSID/password won't make it into the firmware.
info "Cleaning previous build..."
pio run -e "$TARGET" --target clean

info "Building firmware..."
PLATFORMIO_BUILD_FLAGS="$BUILD_FLAGS" pio run -e "$TARGET"
info "Build complete."

# ── Flash ─────────────────────────────────────────────────────────────────────
if [[ "$BUILD_ONLY" == false ]]; then
    UPLOAD_ARGS=(-e "$TARGET" --target upload)
    if [[ -n "$SERIAL_PORT" ]]; then
        info "Flashing to $SERIAL_PORT..."
        UPLOAD_ARGS+=(--upload-port "$SERIAL_PORT")
    else
        info "Flashing (auto-detecting port)..."
        warn "If upload fails, specify the port: --port /dev/ttyUSB0"
    fi
    PLATFORMIO_BUILD_FLAGS="$BUILD_FLAGS" pio run "${UPLOAD_ARGS[@]}"
    info "Flash complete."
else
    warn "Skipping flash (--build-only). Binary: .pio/build/$TARGET/firmware.bin"
fi

# ── Monitor ───────────────────────────────────────────────────────────────────
if [[ "$MONITOR" == true ]]; then
    info "Opening serial monitor (baud: $BAUD). Press Ctrl+C to exit."
    MONITOR_ARGS=(device monitor --baud "$BAUD")
    [[ -n "$SERIAL_PORT" ]] && MONITOR_ARGS+=(--port "$SERIAL_PORT")
    pio "${MONITOR_ARGS[@]}"
fi
