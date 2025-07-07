import gpiozero
import signal
import sys

def cleanup_and_exit(sig, frame):
    print("\nCleaning up...")
    try:
        if 'mybtn' in globals():
            mybtn.close()
        # Don't try to reset - just close individual devices
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup_and_exit)

try:
    # Let gpiozero use its default factory (LGPIOFactory on Pi 5)
    # No need to reset - just create your devices
    
    # Create your button
    mybtn = gpiozero.Button(8)
    print("Button ready on pin 8")
    
    # Your main code here
    
except Exception as e:
    print(f"Error: {e}")
    # If pin 8 is busy, the error will show here
    
finally:
    cleanup_and_exit(None, None)