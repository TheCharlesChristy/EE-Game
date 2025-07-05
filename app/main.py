"""
Multi-Team Gaming System - Main Application Entry Point
Simple Flask application with SocketIO for real-time gaming
"""

import os
import sys
import signal
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Import Flask app factory
from server import create_app

def handle_shutdown(signum, frame):
    """Handle graceful shutdown."""
    print("\nShutting down gracefully...")
    
    # Stop GPIO monitoring
    try:
        from server.gpio_service import gpio_service
        gpio_service.stop_monitoring()
        print("GPIO monitoring stopped")
    except Exception as e:
        print(f"Error stopping GPIO service: {e}")
    
    sys.exit(0)

def main():
    """Main application entry point."""
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Create Flask app and SocketIO
    app, socketio = create_app()
    
    # Configuration
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    debug_mode = True  # Force debug mode for development
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting Multi-Team Gaming System on {host}:{port}")
    print(f"Debug mode: {debug_mode}")
    
    try:
        # Run the application
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug_mode,
            allow_unsafe_werkzeug=True  # For development only
        )
    except KeyboardInterrupt:
        handle_shutdown(signal.SIGINT, None)
    except Exception as e:
        print(f"Error starting application: {e}")
        handle_shutdown(None, None)

if __name__ == '__main__':
    main()