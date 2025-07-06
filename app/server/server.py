"""
Server - Multi-Team Gaming System
=================================

Main Flask server application that initializes page routes.
Keeps everything simple and focused on MVP requirements.

Author: Multi-Team Gaming System Development Team
Version: 1.0.0 MVP
"""

from flask import Flask
from flask_socketio import SocketIO
from EEGame.app.server.page_routes import init_page_routes
from EEGame.app.server.services.data_service import DataService
from EEGame.app.server.services.team_manager import TeamManager
from EEGame.app.server.socketio.socketio_emitter import SocketIOEmitter
from EEGame.app.server.socketio.team_endpoints import create_team_endpoints
from EEGame.app.server.socketio.session_endpoints import create_session_endpoints
from EEGame.app.server.EElogging import setup_logging
import os
import logging
from pathlib import Path

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


class Server:
    """
    Multi-Team Gaming System Server
    
    Encapsulates Flask application configuration and management.
    Provides a clean interface for server initialization and startup.
    """
    
    def __init__(self, host='0.0.0.0', port=5000, debug=True):
        """
        Initialize the server with configuration options.
        
        Args:
            host (str): Host address to bind to
            port (int): Port number to listen on
            debug (bool): Enable debug mode
        """
        self.host = host
        self.port = port
        self.debug = debug
        self.app = None
        self.socketio = None
        self.emitter = None

        data_dir = Path(__file__).parent.parent / 'data'
        self.data_service = DataService(data_dir)
        self.team_manager = TeamManager()
        
    def create_app(self):
        """
        Create and configure the Flask application with SocketIO support.
        
        Returns:
            Flask: Configured Flask application instance
        """
        # Get the path to the app directory (parent of server directory)
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(app_dir, 'assets')
        
        # Configure Flask with custom static folder
        self.app = Flask(__name__, static_folder=assets_dir, static_url_path='/static')
        
        # Basic Flask configuration
        self.app.config['DEBUG'] = self.debug
        self.app.config['SECRET_KEY'] = 'dev-key-change-in-production'
        
        # Initialize SocketIO with additional configuration
        self.socketio = SocketIO(
            self.app, 
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True
        )
        
        # Initialize the SocketIO emitter
        self.emitter = SocketIOEmitter(self.socketio)
        
        # Initialize page routes
        init_page_routes(self.app)
        
        # Initialize SocketIO endpoints
        create_session_endpoints(self.app, self.socketio, self.team_manager, self.emitter)
        create_team_endpoints(self.app, self.socketio, self.team_manager, self.emitter)
        
        return self.app
    
    def run(self):
        """
        Start the Flask development server with SocketIO support.
        """
        if self.app is None:
            self.create_app()
            
        self.socketio.run(
            self.app,
            host=self.host,
            port=self.port,
            debug=self.debug
        )
    
    def get_emitter(self):
        """
        Get the SocketIO emitter instance.
        
        Returns:
            SocketIOEmitter: The emitter instance, or None if not initialized
        """
        return self.emitter
    
    def get_team_manager(self):
        """
        Get the team manager instance.
        
        Returns:
            TeamManager: The team manager instance
        """
        return self.team_manager
    
    def get_data_service(self):
        """
        Get the data service instance.
        
        Returns:
            DataService: The data service instance
        """
        return self.data_service

if __name__ == '__main__':
    """Run the development server."""
    server = Server()
    server.run()
