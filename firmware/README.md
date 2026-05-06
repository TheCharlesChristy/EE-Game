# EE-Game Firmware

## 1. Overview

This directory contains the PlatformIO firmware for EE-Game ESP32 devices. Each device connects to the host Raspberry Pi's local WiFi network, registers with the backend, and sends periodic heartbeat signals. The firmware manages a status LED whose blink pattern reflects the current device state (booting, connecting, connected, fault, in-game).

The default target hardware is the **ESP32-C3 DevKitM-1**. An alternate build target for a generic **ESP32 dev board** (e.g. DOIT ESP32 DevKit v1) is also provided.

Full device protocol (WebSocket client, game event messages) is implemented in EP-09. This scaffold establishes the correct project structure, LED management, WiFi connection handling, and protocol message struct stubs.

SRS references: Section 11.1 (Firmware Stack), Section 8.3 (Device Lifecycle), NFR-016, NFR-017, NFR-020.

## 2. Prerequisites

- **PlatformIO CLI** (`pip install platformio`) or **PlatformIO IDE** (VS Code extension)
- **USB driver** for the target board:
  - ESP32-C3 DevKitM-1: CP210x or CH340 driver depending on board revision
  - ESP32 dev board: CP210x or CH340 driver
- A USB cable with data lines (not charge-only)

Verify your PlatformIO installation:

```
pio --version
```

## 3. Build

Build the default ESP32-C3 environment:

```
pio run
```

Build the alternate ESP32 dev board environment:

```
pio run -e esp32dev
```

Both commands compile all source files and report any errors. No device needs to be connected for a build.

## 4. Flash

Flash to a connected device (default ESP32-C3 environment):

```
pio run --target upload
```

Flash to the alternate environment:

```
pio run --target upload -e esp32dev
```

PlatformIO auto-detects the serial port. If auto-detection fails, specify the port explicitly:

```
pio run --target upload --upload-port /dev/ttyUSB0
```

## 5. Serial Monitor

Open the serial monitor after flashing to view device log output:

```
pio device monitor
```

The monitor baud rate is set to `115200` in `platformio.ini`. Press `Ctrl+C` to exit.

## 6. Board Configuration

Board-specific pin mappings are isolated in `src/config/board_config.h` behind preprocessor guards. This means changing the target board requires editing only that one file, not any application logic.

The status LED pin is defined as `STATUS_LED_PIN`. The default is **GPIO4** for both targets, per SRS FR-027. To change the pin for a given board target, edit the corresponding `#ifdef` block in `src/config/board_config.h`:

```cpp
#ifdef BOARD_ESP32C3
  #define STATUS_LED_PIN     4   // Change this value to remap the LED pin
  #define STATUS_LED_ACTIVE  HIGH
```

If you are adding support for a new board variant, add a new `#elif defined(BOARD_XXXXX)` block and add the corresponding `-DBOARD_XXXXX` build flag to a new `[env:xxxxx]` section in `platformio.ini`.

## 7. WiFi Credentials

WiFi credentials are injected at build time via `build_flags` in `platformio.ini`. They must never be hardcoded in committed source files.

Add the following to the relevant `[env:*]` section in `platformio.ini` (or in a local `platformio_local.ini` excluded from version control):

```ini
build_flags =
    -DBOARD_ESP32C3
    -DCORE_DEBUG_LEVEL=3
    -DWIFI_SSID=\"your-network-name\"
    -DWIFI_PASSWORD=\"your-password\"
```

If `WIFI_SSID` and `WIFI_PASSWORD` are not defined via build flags, `src/main.cpp` falls back to the placeholder defaults `"ee-game"` and `"changeme"`. These placeholder values will not connect to a real network; they exist only so the project compiles without credentials present.

For the hosted Raspberry Pi access point the expected SSID is `ee-game` with a site-specific password configured during deployment (see `docs/` for deployment runbooks).

## 8. Protocol Note

The C++ structs in `src/protocol/message_types.h` mirror the JSON Schema definitions in `shared/schemas/v1/`. Field names, required fields, and the protocol version string must remain in sync with those schemas and with `shared/constants/protocol.py`.

The protocol version is defined as:

```cpp
static constexpr char PROTOCOL_VERSION[] = "1";
```

This must match the `PROTOCOL_VERSION` constant in `shared/constants/protocol.py` at all times. If the protocol version is incremented during EP-09 or later, both files must be updated together.

SRS reference: IF-001 through IF-006, Section 11.3.
