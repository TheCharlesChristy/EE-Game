import gpiozero
import RPi.GPIO as GPIO

pin = 27
try:
    # Try setting pin 27 as an output
    test_pin = gpiozero.LED(pin)
    print(f"Pin {pin} is available!")
    test_pin.close()  # Close it immediately
except Exception as e:
    print(f"Pin {pin} is in use or unavailable: {e}")


# Function to check for available GPIO pins
def check_available_pins():
    # List of all possible GPIO pins on the Raspberry Pi (BCM numbering)
    all_pins = [i for i in range(2, 28)]  # Raspberry Pi 5 has GPIO pins 2-27 available
    available_pins = []

    for pin in all_pins:
        try:
            # Check if the pin is in use by attempting to set it up as an output pin
            pin_device = gpiozero.LED(pin)
            pin_device.close()  # Close it immediately to release it
            available_pins.append(pin)
        except Exception as e:
            print(f"Pin {pin} is in use or unavailable: {e}")
            # If an exception occurs, the pin is likely in use
            continue

    return available_pins

# Clean up GPIO settings
GPIO.cleanup()

# Check which pins are available
available_pins = check_available_pins()
print("Available GPIO Pins:", available_pins)
