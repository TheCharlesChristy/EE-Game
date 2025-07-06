import logging

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("EElogging.log"),
            logging.StreamHandler()
        ]
    )
    logging.getLogger("gpiozero").setLevel(logging.WARNING)  # Reduce noise from gpiozero
    logging.getLogger("picamera").setLevel(logging.WARNING)  # Reduce noise from picamera