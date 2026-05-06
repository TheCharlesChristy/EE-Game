#pragma once
/**
 * Board-specific configuration.
 *
 * Pin mappings and feature switches are isolated here so that changing the
 * target board does not require rewriting common application code.
 * SRS reference: NFR-017, FR-027.
 */

#ifdef BOARD_ESP32C3
  // ESP32-C3 DevKitM-1
  // Status LED: onboard RGB LED on GPIO8 on some revisions; use GPIO4 as
  // project default per SRS FR-027.
  #define STATUS_LED_PIN     4
  #define STATUS_LED_ACTIVE  HIGH
  #define INPUT_BUTTON_PIN   5
  #define INPUT_ANALOG_PIN   0

#elif defined(BOARD_ESP32DEV)
  // Generic ESP32 dev board (e.g. DOIT ESP32 DevKit v1)
  #define STATUS_LED_PIN     4
  #define STATUS_LED_ACTIVE  HIGH
  #define INPUT_BUTTON_PIN   5
  #define INPUT_ANALOG_PIN   34

#else
  #error "Unknown board target. Add a -DBOARD_XXX build flag in platformio.ini."
#endif
