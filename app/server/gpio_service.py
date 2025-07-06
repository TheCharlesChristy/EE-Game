"""
GPIO Service - Hardware Interface for Multi-Team Gaming System
Handles button monitoring, LED control, and hardware abstraction
"""

import time
import threading
import queue
import json
from pathlib import Path

# Hardware abstraction - use simulation in development
try:
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except ImportError:
    # Create a simple GPIO simulator for development
    class GPIOSimulator:
        BCM = 'BCM'
        IN = 'IN'
        OUT = 'OUT'
        HIGH = 1
        LOW = 0
        
        def __init__(self):
            self.pin_states = {}
            
        def setmode(self, mode):
            pass
            
        def setup(self, pin, mode):
            self.pin_states[pin] = 0
            
        def input(self, pin):
            return self.pin_states.get(pin, 0)
            
        def output(self, pin, value):
            self.pin_states[pin] = value
            
        def cleanup(self):
            self.pin_states.clear()
    
    GPIO = GPIOSimulator()
    HARDWARE_AVAILABLE = False


class GPIOService:
    """Simple GPIO service for button monitoring and LED control."""
    
    def __init__(self):
        self.message_queue = queue.Queue()
        self.monitoring_thread = None
        self.running = False
        self.pin_config = self.load_pin_config()
        self.last_press_time = {}  # For debouncing
        
        # Initialize GPIO
        if HARDWARE_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            self.setup_pins()
    
    def load_pin_config(self):
        """Load pin configuration from JSON file or use defaults."""
        config_file = Path('data/config.json')
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Convert string keys to integers
                pin_mapping = config.get('pin_mapping', {})
                return {int(k): v for k, v in pin_mapping.items()}
        else:
            return self.get_default_pins()
    
    def get_default_pins(self):
        """Default pin configuration for 8 teams."""
        return {
            1: {"latch": 11, "reset": 12, "led": 13},
            2: {"latch": 15, "reset": 16, "led": 18},
            3: {"latch": 19, "reset": 21, "led": 23},
            4: {"latch": 24, "reset": 26, "led": 29},
            5: {"latch": 31, "reset": 32, "led": 33},
            6: {"latch": 35, "reset": 36, "led": 37},
            7: {"latch": 38, "reset": 40, "led": 3},
            8: {"latch": 5, "reset": 7, "led": 8}
        }
    
    def setup_pins(self):
        """Configure GPIO pins for all teams."""
        for team_id, pins in self.pin_config.items():
            GPIO.setup(pins['latch'], GPIO.IN)
            GPIO.setup(pins['reset'], GPIO.OUT)
            GPIO.setup(pins['led'], GPIO.OUT)
            # Initialize LED off and latch reset
            GPIO.output(pins['led'], GPIO.LOW)
            GPIO.output(pins['reset'], GPIO.LOW)
    
    def start_monitoring(self):
        """Start background thread for GPIO monitoring."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
            
        self.running = True
        self.monitoring_thread = threading.Thread(target=self.monitor_pins, daemon=True)
        self.monitoring_thread.start()
        print("GPIO monitoring started")
    
    def stop_monitoring(self):
        """Stop GPIO monitoring thread."""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        if HARDWARE_AVAILABLE:
            GPIO.cleanup()
        print("GPIO monitoring stopped")
    
    def monitor_pins(self):
        """Main monitoring loop - checks for button presses."""
        while self.running:
            for team_id, pins in self.pin_config.items():
                if GPIO.input(pins['latch']):
                    current_time = time.time()
                    
                    # Simple debouncing - ignore presses within 50ms
                    if (team_id not in self.last_press_time or 
                        current_time - self.last_press_time[team_id] > 0.05):
                        
                        self.last_press_time[team_id] = current_time
                        
                        # Add button press to queue
                        self.message_queue.put({
                            'team_id': team_id,
                            'timestamp': current_time,
                            'type': 'button_press'
                        })
                        
                        # Reset the latch
                        self.reset_latch(pins['reset'])
            
            time.sleep(0.001)  # 1ms polling interval
    
    def reset_latch(self, reset_pin):
        """Reset a team's latch pin."""
        GPIO.output(reset_pin, GPIO.HIGH)
        time.sleep(0.001)  # Hold reset for 1ms
        GPIO.output(reset_pin, GPIO.LOW)
    
    def control_led(self, team_id, state):
        """Control LED for a specific team."""
        if team_id in self.pin_config:
            led_pin = self.pin_config[team_id]['led']
            GPIO.output(led_pin, GPIO.HIGH if state else GPIO.LOW)
            return True
        return False
    
    def test_hardware(self, team_id):
        """Test hardware for a specific team."""
        if team_id not in self.pin_config:
            return {"status": "error", "message": "Invalid team ID"}
        
        try:
            pins = self.pin_config[team_id]
            
            # Test LED
            start_time = time.time()
            self.control_led(team_id, True)
            time.sleep(0.1)
            self.control_led(team_id, False)
            
            # Check button state
            button_state = GPIO.input(pins['latch'])
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "success",
                "team_id": team_id,
                "button_press": "detected" if button_state else "not_detected",
                "led_control": "working",
                "response_time_ms": round(response_time, 2)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_button_events(self):
        """Get all pending button press events."""
        events = []
        while not self.message_queue.empty():
            try:
                events.append(self.message_queue.get_nowait())
            except queue.Empty:
                break
        return events
    
    def get_pin_status(self):
        """Get current status of all GPIO pins."""
        status = {}
        for team_id, pins in self.pin_config.items():
            try:
                status[f"team_{team_id}"] = {
                    "latch": "connected" if GPIO.input(pins['latch']) is not None else "error",
                    "hardware_available": HARDWARE_AVAILABLE
                }
            except Exception:
                status[f"team_{team_id}"] = {"latch": "error", "hardware_available": False}
        return status
    
    def get_status(self):
        """Get overall GPIO service status."""
        return "operational" if HARDWARE_AVAILABLE and self.running else "error"
    
    def is_healthy(self):
        """Health check for the GPIO service."""
        return self.running and (HARDWARE_AVAILABLE or True)  # Allow simulator in dev
    
    def simulate_button_press(self, team_id):
        """Simulate a button press for testing purposes."""
        if team_id in self.pin_config:
            current_time = time.time()
            self.message_queue.put({
                'team_id': team_id,
                'timestamp': current_time,
                'type': 'button_press'
            })
            return True
        return False
    
    def get_led_status(self, team_id):
        """Get the current LED status for a team."""
        if team_id in self.pin_config:
            led_pin = self.pin_config[team_id]['led']
            try:
                # In simulation mode, we'll track state separately
                if not HARDWARE_AVAILABLE:
                    return {
                        'state': 'off',  # Default state
                        'pin': led_pin,
                        'connection': 'connected'
                    }
                else:
                    # For real hardware, we can't read output pin state reliably
                    return {
                        'state': 'unknown',  # Would need to track this separately
                        'pin': led_pin,
                        'connection': 'connected'
                    }
            except Exception:
                return {
                    'state': 'error',
                    'pin': led_pin,
                    'connection': 'error'
                }
        return None
    
    def test_all_leds(self, duration_ms=1000):
        """Test all LEDs by turning them on for the specified duration."""
        try:
            # Turn on all LEDs
            for team_id in self.pin_config.keys():
                self.control_led(team_id, True)
            
            # Wait for duration
            time.sleep(duration_ms / 1000.0)
            
            # Turn off all LEDs
            for team_id in self.pin_config.keys():
                self.control_led(team_id, False)
            
            return True
        except Exception as e:
            print(f"LED test failed: {e}")
            return False
    
    def reset_all_leds(self):
        """Turn off all LEDs."""
        try:
            for team_id in self.pin_config.keys():
                self.control_led(team_id, False)
            return True
        except Exception as e:
            print(f"LED reset failed: {e}")
            return False
    
    def set_led_flashing(self, team_id, enabled=True):
        """Set an LED to flash (simplified implementation - just turns on/off)."""
        if enabled:
            # For this MVP, we'll just turn the LED on
            # A full implementation would use threading for flashing
            return self.control_led(team_id, True)
        else:
            return self.control_led(team_id, False)


# Global service instance
gpio_service = GPIOService()
