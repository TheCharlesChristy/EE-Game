from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from pathlib import Path
from gpiozero import Button, LED
import time
from typing import List, Dict
from EEGame.app.server.Teams.pin import Pin
import threading

class Team:
    """Represents a team in the Multi-Team Gaming System."""
    
    def __init__(self, team_id: str, name: str, team_color: str, latch_pin: int, reset_pin: int, led_pin: int):
        """
        Initialize the Team class.
        
        Args:
            team_id: Unique identifier for the team.
            name: Name of the team.
            pins: Dictionary of pin names and their corresponding GPIO pin numbers.
        """
        self.team_id = team_id
        self.name = name
        self.team_color = team_color

        self.latch_pin = self.create_latch_pin(latch_pin)
        self.reset_pin = self.create_reset_pin(reset_pin)
        self.led_pin = self.create_led_pin(led_pin)
        
    def create_latch_pin(self, pin_number: int, callback: Optional[callable] = None) -> Pin:
        """
        Create a latch pin for the team.
        """
        return Pin(pin_number, mode="input", board_pin=True, callback=callback, pull_up_down="down", initial_value=False)
    
    def create_reset_pin(self, pin_number: int) -> Pin:
        """
        Create a reset pin for the team.
        """
        return Pin(pin_number, mode="output", board_pin=True)
    
    def create_led_pin(self, pin_number: int) -> Pin:
        """
        Create an LED pin for the team.
        """
        return Pin(pin_number, mode="output", board_pin=True)
    
    def update_pins(self, latch_pin: Optional[int] = None, reset_pin: Optional[int] = None, led_pin: Optional[int] = None) -> None:
        """
        Update the pins for the team.
        
        Args:
            latch_pin: New GPIO pin number for the latch pin.
            reset_pin: New GPIO pin number for the reset pin.
            led_pin: New GPIO pin number for the LED pin.
        """
        if latch_pin is not None:
            # remove the old latch pin if it exists so it doesnt call any callbacks
            if hasattr(self, 'latch_pin'):
                self.latch_pin.close()
            self.latch_pin = self.create_latch_pin(latch_pin)
        if reset_pin is not None:
            if hasattr(self, 'reset_pin'):
                self.reset_pin.close()
            self.reset_pin = self.create_reset_pin(reset_pin)
        if led_pin is not None:
            if hasattr(self, 'led_pin'):
                self.led_pin.close()
            self.led_pin = self.create_led_pin(led_pin)

    def set_callback(self, callback: Optional[callable] = None, callback_args: Optional[List[Any]] = None) -> None:
        """
        Set a callback for the latch pin.
        
        Args:
            callback: Function to call when the latch pin is pressed.
        """
        if hasattr(self, 'latch_pin'):
            self.latch_pin.register_callback(callback, callback_args=callback_args)

    def remove_callback(self) -> None:
        """
        Remove the callback from the latch pin.
        """
        if hasattr(self, 'latch_pin'):
            self.latch_pin.register_callback(lambda: None) # Set to a function that does nothing

    def close(self) -> None:
        """
        Close the GPIO pins for the team.
        """
        if hasattr(self, 'latch_pin'):
            self.latch_pin.close()
        if hasattr(self, 'reset_pin'):
            self.reset_pin.close()
        if hasattr(self, 'led_pin'):
            self.led_pin.close()

    def turn_on_led(self) -> None:
        """
        Turn on the LED pin.
        """
        if hasattr(self, 'led_pin'):
            self.led_pin.turn_on()

    def turn_off_led(self) -> None:
        """
        Turn off the LED pin.
        """
        if hasattr(self, 'led_pin'):
            self.led_pin.turn_off()

    def toggle_led(self) -> None:
        """
        Toggle the LED pin.
        """
        if hasattr(self, 'led_pin'):
            if self.led_pin.gpio_pin.is_active:
                self.led_pin.turn_off()
            else:
                self.led_pin.turn_on()

    def flash_led(self, flash_duration: float, pulse_length: float) -> None:
        """
        Flash the LED pin for a specified duration.
        
        Args:
            duration: Duration to flash the LED in seconds.
        """
        
        def _flash():
            if hasattr(self, 'led_pin'):
                end_time = time.time() + flash_duration
                while time.time() < end_time:
                    self.led_pin.turn_on()
                    time.sleep(pulse_length)
                    self.led_pin.turn_off()
                    time.sleep(pulse_length)
        
        thread = threading.Thread(target=_flash)
        thread.start()
        self.led_pin.turn_off()

    def reset_latch(self) -> None:
        """
        Reset the latch pin.
        """
        if hasattr(self, 'reset_pin'):
            self.reset_pin.turn_on()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the team object to a dictionary for JSON serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the team with current hardware states.
        """
        return {
            'team_id': self.team_id,
            'name': self.name,
            'team_color': self.team_color,
            'latch_pin': self.latch_pin.pin_number if hasattr(self, 'latch_pin') else None,
            'reset_pin': self.reset_pin.pin_number if hasattr(self, 'reset_pin') else None,
            'led_pin': self.led_pin.pin_number if hasattr(self, 'led_pin') else None,
            'latch_state': self.latch_pin.gpio_pin.is_active if hasattr(self, 'latch_pin') and hasattr(self.latch_pin, 'gpio_pin') else False,
            'led_state': self.led_pin.gpio_pin.is_active if hasattr(self, 'led_pin') and hasattr(self.led_pin, 'gpio_pin') else False
        }