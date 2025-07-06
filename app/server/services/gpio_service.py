"""A service running on a Raspberry Pi to monitor GPIO pins and send interupts to the server to process said events."""

from gpiozero import Button, LED
import time
from typing import List, Dict
from app.server.EEtypes import Pin, TeamPins
import logging
from app.server.EElogging import setup_logging

# Set up logging
setup_logging()

class GPIOService:
    """Service to monitor GPIO pins and handle interrupts."""
    
    def __init__(self, pins: list[Pin] = [], team_pins: list[TeamPins] = []) -> None:
        """Initialize the GPIO service with a list of Pin configurations."""
        self.pins: List[Pin] = []
        self.input_pins: List[Pin] = []
        self.output_pins: List[Pin] = []
        self.gpio_available = False
        self.gpio_objects: Dict[int, any] = {}  # Store gpiozero objects
        self.logger = logging.getLogger(__name__)

        self.event_queue = []

        self.set_pins(pins)

        for team in team_pins:
            if not isinstance(team, TeamPins):
                raise ValueError("team_pins must be an instance of TeamPins")
            # Add team pins to the service
            self.add_team_pins(team)

    def is_gpio_available(self) -> bool:
        """Check if GPIO is available and properly initialized."""
        return self.gpio_available

        
    def set_pins(self, pins: list[Pin]) -> None:
        """Set the GPIO pins to monitor."""
            
        self.pins = pins
        self.input_pins: List[Pin] = []
        self.output_pins: List[Pin] = []
        self.set_input_pins()
        self.set_output_pins()
        self.gpio_available = True


    def set_input_pins(self) -> None:
        """Set the GPIO pins to input mode."""
            
        self.input_pins = [pin for pin in self.pins if pin.mode == "input"]
        for pin in self.input_pins:
            # Create Button object with appropriate pull resistor
            pull_up = None
            if pin.pull_up_down == "up":
                pull_up = True
            elif pin.pull_up_down == "down":
                pull_up = False
            
            button = Button(pin.get_pin_number(), pull_up=pull_up, bounce_time=0.05)

            self.gpio_objects[pin.get_pin_number()] = button
            
            if pin.callback:
                # Set up both press and release callbacks
                button.when_pressed = lambda channel=pin.get_pin_number(): self.handle_pin_event(channel)
    
    def get_pin(self, pin_number: int) -> Pin:
        """Get a Pin object by its pin number."""
        for pin in self.pins:
            if pin.pin_number == pin_number:
                return pin
        raise ValueError(f"Pin {pin_number} not found in configured pins.")
    
    def set_output_pins(self) -> None:
        """Set the GPIO pins to output mode."""
        self.output_pins = [pin for pin in self.pins if pin.mode == "output"]

        for pin in self.output_pins:

            led = LED(pin.get_pin_number())

            self.gpio_objects[pin.get_pin_number()] = led

            if pin.initial_value is not None:
                if pin.initial_value:
                    led.on()
                else:
                    led.off()
                pin.state = pin.initial_value

    def set_output_pin(self, pin: Pin, value: bool) -> None:
        """Set the value of an output pin."""            
        pin_number = pin.get_pin_number()
        
        led = self.gpio_objects.get(pin_number)

        if led:
            # self.logger.debug(f"Setting pin {pin_number} state to {'HIGH' if value else 'LOW'}")
            if value:
                led.on()
            else:
                led.off()

    def get_pin_state(self, pin: Pin) -> bool:
        """Get the state of an output pin."""
        pin_number = pin.get_pin_number()
        
        if pin.mode == "output":
            led = self.gpio_objects.get(pin_number)
            if led:
                return led.is_lit
            else:
                raise ValueError(f"Pin {pin_number} is not configured as an output pin.")
        elif pin.mode == "input":
            button = self.gpio_objects.get(pin_number)
            if button:
                return button.is_pressed
            else:
                raise ValueError(f"Pin {pin_number} is not configured as an input pin.")

    def handle_pin_event(self, channel: int) -> None:
        """Handle GPIO pin events."""
        for pin in self.input_pins:
            if pin.get_pin_number() == channel and pin.callback:
                self.logger.debug(f"Pin {channel} pressed, calling callback.")
                pin.callback(channel)

    def cleanup(self) -> None:
        """Clean up GPIO settings."""
        try:
            # Close all gpiozero objects
            for gpio_obj in self.gpio_objects.values():
                if hasattr(gpio_obj, 'close'):
                    gpio_obj.close()
        except Exception as e:
            print(f"Warning: GPIO cleanup failed: {e}")
        
        # Reset internal state
        self.pins = []
        self.input_pins = []
        self.output_pins = []
        self.gpio_objects = {}
        self.gpio_available = False

    def log_pin(self, pin: Pin) -> None:
        """Log pin configuration and state."""
        pin_number = pin.get_pin_number()
        self.logger.info(f"Pin {pin_number} - Mode: {pin.mode}, Board Pin: {pin.board_pin}, "
                         f"Callback: {'set' if pin.callback else 'not set'}, "
                         f"Pull Up/Down: {pin.pull_up_down}, Initial Value: {pin.initial_value}")
        state = self.get_pin_state(pin)
        self.logger.info(f"Pin {pin_number} state: {'HIGH' if state else 'LOW'}")

    
    def reset_team_latch(self, team_pins: TeamPins) -> None:
        """Reset the latch pin for a team."""
        # Send a pulse to the reset pin
        reset_pin = team_pins.reset_pin.get_pin_number()

        if reset_pin in self.gpio_objects:
            reset_led = self.gpio_objects[reset_pin]
            self.logger.debug(f"Resetting latch pin {reset_pin}")

            def pulse_reset_pin():
                """Pulse the reset pin in a separate thread."""
                reset_led.on()
                time.sleep(0.1)
                reset_led.off()

            # Run the pulse in a separate thread to avoid blocking the GPIO callback
            import threading
            threading.Thread(target=pulse_reset_pin, daemon=True).start()

    def toggle_team_led(self, team_pins: TeamPins) -> None:
        """Toggle the LED pin for a team."""
        led_pin = team_pins.led_pin.get_pin_number()

        if led_pin in self.gpio_objects:
            led = self.gpio_objects[led_pin]
            self.logger.debug(f"Toggling LED pin {led_pin}")
            if led.is_lit:
                led.off()
            else:
                led.on()
        else:
            self.logger.warning(f"LED pin {led_pin} not found in GPIO objects.")

    def turn_on_team_led(self, team_pins: TeamPins) -> None:
        """Turn on the LED pin for a team."""
        led_pin = team_pins.led_pin.get_pin_number()

        if led_pin in self.gpio_objects:
            led = self.gpio_objects[led_pin]
            self.logger.debug(f"Turning on LED pin {led_pin}")
            led.on()
        else:
            self.logger.warning(f"LED pin {led_pin} not found in GPIO objects.")

    def turn_off_team_led(self, team_pins: TeamPins) -> None:
        """Turn off the LED pin for a team."""
        led_pin = team_pins.led_pin.get_pin_number()

        if led_pin in self.gpio_objects:
            led = self.gpio_objects[led_pin]
            self.logger.debug(f"Turning off LED pin {led_pin}")
            led.off()
        else:
            self.logger.warning(f"LED pin {led_pin} not found in GPIO objects.")

    def add_pin(self, pin: Pin) -> None:
        """Add a new pin to the service."""
        if not isinstance(pin, Pin):
            raise ValueError("pin must be an instance of Pin")
        
        self.pins.append(pin)
        
        if pin.mode == "input":
            self.input_pins.append(pin)
            self.set_input_pins()
        elif pin.mode == "output":
            self.output_pins.append(pin)
            self.set_output_pins()
        
        self.gpio_objects[pin.get_pin_number()] = None

    def remove_pin(self, pin_number: int) -> None:
        """Remove a pin from the service."""
        pin = self.get_pin(pin_number)
        if pin in self.pins:
            self.pins.remove(pin)
            if pin in self.input_pins:
                self.input_pins.remove(pin)
            if pin in self.output_pins:
                self.output_pins.remove(pin)
            del self.gpio_objects[pin.get_pin_number()]

    def add_team_pins(self, team_pins: TeamPins) -> None:
        """Add a team's GPIO pins to the service."""
        if not isinstance(team_pins, TeamPins):
            raise ValueError("team_pins must be an instance of TeamPins")
        
        # Add latch pin
        self.add_pin(team_pins.latch_pin)

        # Add reset pin
        self.add_pin(team_pins.reset_pin)

        # Add LED pin
        self.add_pin(team_pins.led_pin)

    def remove_team_pins(self, team_pins: TeamPins) -> None:
        """Remove a team's GPIO pins from the service."""
        if not isinstance(team_pins, TeamPins):
            raise ValueError("team_pins must be an instance of TeamPins")
        
        # Remove latch pin
        self.remove_pin(team_pins.latch_pin.pin_number)

        # Remove reset pin
        self.remove_pin(team_pins.reset_pin.pin_number)

        # Remove LED pin
        self.remove_pin(team_pins.led_pin.pin_number)
        
            


if __name__ == "__main__":

    def pin_callback(channel):
        gpio_service.reset_team_latch(team1_pins)

    pins = [
        Pin(pin_number=22, board_pin=True, mode="input", callback=pin_callback, pull_up_down="down"),
        Pin(pin_number=24, board_pin=True, mode="output", initial_value=False),
        Pin(pin_number=40, board_pin=True, mode="output", initial_value=False)
    ]

    team1_pins = TeamPins(
        latch_pin=pins[0],
        reset_pin=pins[2],
        led_pin=pins[1]
    )

    gpio_service = GPIOService(pins)
    try:
        print("GPIO service started. Press Ctrl+C to stop.")
        while True:
            time.sleep(0.1)  # Keep the service running
            # Flash output pin every 2 seconds
            pin = gpio_service.get_pin(24)
            pin_state = gpio_service.get_pin_state(pin)
            gpio_service.set_output_pin(pin, not pin_state)
    except KeyboardInterrupt:
        gpio_service.cleanup()
        print("GPIO service stopped.")