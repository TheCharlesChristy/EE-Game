# Firmware Tests

Firmware unit tests are implemented using PlatformIO's native test framework in EP-09. This directory is a placeholder for the test runner.

Tests will be placed in subdirectories following PlatformIO conventions (e.g. `test/test_led_manager/`, `test/test_protocol/`). Each test directory contains a `main.cpp` with `RUN_TEST` calls using the Unity test framework bundled with PlatformIO.

To run tests once implemented:

```
pio test -e esp32-c3
```
