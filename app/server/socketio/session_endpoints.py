"""
Session Endpoints - Multi-Team Gaming System
===========================================

SocketIO endpoints for session management including connection and disconnection handling.
Provides centralized session management functionality.

Author: Multi-Team Gaming System Development Team
Version: 1.0.0 MVP
"""

import logging
from flask_socketio import emit
from EEGame.app.server.services.team_manager import TeamManager
from EEGame.app.server.EElogging import setup_logging
from EEGame.app.server.socketio.socketio_emitter import SocketIOEmitter

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


def create_session_endpoints(app, socketio, team_manager: TeamManager, emitter: SocketIOEmitter):
    """
    Create SocketIO endpoints for session management.
    
    Args:
        app: Flask application instance
        socketio: SocketIO instance
        team_manager: TeamManager instance for team operations
        emitter: SocketIOEmitter instance for handling emissions
    """

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        logger.info("Client connected")
        emit('connection_status', {'status': 'connected', 'message': 'Successfully connected to server'})
        
        # Send current team list to newly connected client
        teams = team_manager.get_all_teams()
        emitter.emit_teams_list([team.to_dict() for team in teams.values()])

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        logger.info("Client disconnected")

    @socketio.on('ping')
    def handle_ping():
        """Handle ping requests for connection testing."""
        logger.debug("Ping received")
        emit('pong', {'timestamp': __import__('time').time()})
