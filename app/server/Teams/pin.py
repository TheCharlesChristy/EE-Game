from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from pathlib import Path
from gpiozero import Button, LED
import time
from typing import List, Dict

board_to_bcm = {
    3: 2,   # BCM 2
    5: 3,   # BCM 3
    7: 4,   # BCM 4
    8: 14,  # BCM 14
    10: 15, # BCM 15
    11: 17, # BCM 17
    12: 18, # BCM 18
    13: 27, # BCM 27
    15: 22, # BCM 22
    16: 23, # BCM 23
    18: 24, # BCM 24
    19: 10, # BCM 10 (MOSI)
    21: 9,  # BCM 9 (MISO)
    22: 25, # BCM 25
    23: 11, # BCM 11 (SCLK)
    24: 8,   # BCM8 (CE0)
    26: 7,   # BCM7 (CE1)
    29: 5,   # BCM5
    31: 6,   # BCM6
    32: 12,  # BCM12
    33: 13,  # BCM13
    35: 19,  # BCM19
    36: 16,  # BCM16
    37: 26,  # BCM26
    38: 20,  # BCM20
    40: 21,  # BCM21
}

class Pin:
    """Represents a GPIO pin configuration."""
    def __init__(
        self,
        pin_number: int,
        mode: str = "input",
        board_pin: bool = False,
        callback: Optional[callable] = None,
        pull_up_down: Optional[str] = None,
        initial_value: Optional[bool] = None
    ):
        self.pin_number = pin_number # Pin number in board
        self.mode = mode # "input" or "output"
        self.board_pin = board_pin
        self.callback = callback
        self.pull_up_down = pull_up_down
        self.initial_value = initial_value
        self.board_to_bcm = board_to_bcm  # Mapping from board pin numbers to BCM pin numbers

        if mode == "input":
            self.gpio_pin = Button(self.get_pin_number(), pull_up=self.pull_up_down == "up")
            if callback:
                self.gpio_pin.when_pressed = callback
        elif mode == "output":
            self.gpio_pin = LED(self.get_pin_number())
            if initial_value is not None:
                self.gpio_pin.value = initial_value

    def get_pin_number(self) -> int:
        """Get the pin number in BCM format."""
        if self.board_pin:
            return self.board_to_bcm.get(self.pin_number, self.pin_number)
        return self.pin_number
    
    def set_output(self, value: bool):
        """Set the output value for output pins."""
        if self.mode == "output":
            if value:
                self.gpio_pin.on()
            else:
                self.gpio_pin.off()
        else:
            raise ValueError("Cannot set output on an input pin")

    def turn_on(self):
        """Turn on the pin (for output pins)."""
        self.set_output(True)

    def turn_off(self):
        """Turn off the pin (for output pins)."""
        self.set_output(False)

    def register_callback(self, callback: Union[callable, None] = None, callback_args: Optional[List[Any]] = None):
        """Register a callback for input pins."""
        if self.mode == "input":
            if callback and isinstance(self.gpio_pin, Button):
                if callback_args:
                    self.gpio_pin.when_pressed = lambda: callback(*callback_args)
                else:
                    self.gpio_pin.when_pressed = callback
                
            else:
                self.gpio_pin.when_pressed = None
        else:
            raise ValueError("Cannot register callback on an output pin")

    def close(self):
        """Close the pin and release resources."""
        if hasattr(self, 'gpio_pin'):
            self.gpio_pin.close()
            del self.gpio_pin
