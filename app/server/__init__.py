"""
Flask Application Factory - Multi-Team Gaming System
Simple Flask app with SocketIO for real-time communication
"""

from flask import Flask
from flask_socketio import SocketIO
from pathlib import Path
import logging

def create_app():
    """Create and configure the Flask application with SocketIO support."""

    assets_path = Path(__file__).parent.parent / 'assets'
    print(f"Assets path: {assets_path}")
    print(f"Assets path exists: {assets_path.exists()}")
    print(f"Assets path absolute: {assets_path.absolute()}")
    templates_path = Path(__file__).parent.parent / 'templates'

    app = Flask(__name__, static_folder=str(assets_path), template_folder=str(templates_path))
    app.config['SECRET_KEY'] = 'gaming-system-secret-key'
    app.config['DEBUG'] = True
    
    # Enable detailed logging
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    
    # Add error handler
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return f"Internal Server Error: {error}", 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f"404 error: {error}")
        return f"Not Found: {error}", 404
    
    # Initialize SocketIO with threading mode for simplicity
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Import and register routes
    from . import routes
    routes.init_app(app, socketio)
    
    # Initialize services
    from .gpio_service import gpio_service
    from .websocket_service import websocket_service
    
    # Start GPIO monitoring if not in testing mode
    if not app.config.get('TESTING'):
        gpio_service.start_monitoring()
    
    # Initialize WebSocket service
    websocket_service.init_socketio(socketio)
    
    return app, socketio
