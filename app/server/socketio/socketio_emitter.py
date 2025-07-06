"""
SocketIO Emitter - Multi-Team Gaming System
==========================================

Centralized class for handling all SocketIO emissions.
Provides a clean interface for broadcasting events to clients.

Author: Multi-Team Gaming System Development Team
Version: 1.0.0 MVP
"""

import logging
from flask_socketio import emit
from typing import Dict, Any, List, Optional
from EEGame.app.server.EElogging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


class SocketIOEmitter:
    """
    Centralized handler for all SocketIO emissions.
    
    This class provides methods for emitting various team-related events
    to connected clients, ensuring consistent event structure and logging.
    """
    
    def __init__(self, socketio):
        """
        Initialize the SocketIO emitter.
        
        Args:
            socketio: The SocketIO instance for broadcasting events
        """
        self.socketio = socketio
    
    def emit_team_created(self, team_dict: Dict[str, Any]) -> None:
        """
        Emit team created event to the requesting client.
        
        Args:
            team_dict: Dictionary representation of the created team
        """
        try:
            emit('team_created', team_dict)
            logger.debug(f"Emitted team_created event for team: {team_dict.get('team_id')}")
        except Exception as e:
            logger.error(f"Error emitting team_created event: {str(e)}")
    
    def emit_team_updated(self, team_dict: Dict[str, Any]) -> None:
        """
        Emit team updated event to the requesting client.
        
        Args:
            team_dict: Dictionary representation of the updated team
        """
        try:
            emit('team_updated', team_dict)
            logger.debug(f"Emitted team_updated event for team: {team_dict.get('team_id')}")
        except Exception as e:
            logger.error(f"Error emitting team_updated event: {str(e)}")
    
    def emit_team_deleted(self, team_id: str) -> None:
        """
        Emit team deleted event to the requesting client.
        
        Args:
            team_id: ID of the deleted team
        """
        try:
            emit('team_deleted', {'team_id': team_id})
            logger.debug(f"Emitted team_deleted event for team: {team_id}")
        except Exception as e:
            logger.error(f"Error emitting team_deleted event: {str(e)}")
    
    def emit_teams_list(self, teams_list: List[Dict[str, Any]]) -> None:
        """
        Emit teams list to the requesting client.
        
        Args:
            teams_list: List of team dictionaries
        """
        try:
            emit('teams_list', {'teams': teams_list})
            logger.debug(f"Emitted teams_list event with {len(teams_list)} teams")
        except Exception as e:
            logger.error(f"Error emitting teams_list event: {str(e)}")
    
    def emit_team_data(self, team_dict: Dict[str, Any]) -> None:
        """
        Emit single team data to the requesting client.
        
        Args:
            team_dict: Dictionary representation of the team
        """
        try:
            emit('team_data', team_dict)
            logger.debug(f"Emitted team_data event for team: {team_dict.get('team_id')}")
        except Exception as e:
            logger.error(f"Error emitting team_data event: {str(e)}")
    
    def emit_team_status(self, status: Dict[str, Any]) -> None:
        """
        Emit team hardware status to the requesting client.
        
        Args:
            status: Dictionary containing team status information
        """
        try:
            emit('team_status', status)
            logger.debug(f"Emitted team_status event for team: {status.get('team_id')}")
        except Exception as e:
            logger.error(f"Error emitting team_status event: {str(e)}")
    
    def emit_team_error(self, message: str) -> None:
        """
        Emit team error to the requesting client.
        
        Args:
            message: Error message to send
        """
        try:
            emit('team_error', {'message': message})
            logger.warning(f"Emitted team_error event: {message}")
        except Exception as e:
            logger.error(f"Error emitting team_error event: {str(e)}")
    
    def broadcast_team_list_updated(self, teams_list: List[Dict[str, Any]]) -> None:
        """
        Broadcast team list update to all connected clients.
        
        Args:
            teams_list: List of team dictionaries
        """
        try:
            self.socketio.emit('team_list_updated', {'teams': teams_list})
            logger.debug(f"Broadcasted team_list_updated event with {len(teams_list)} teams")
        except Exception as e:
            logger.error(f"Error broadcasting team_list_updated event: {str(e)}")
    
    def broadcast_led_state_changed(self, team_id: str, led_state: bool) -> None:
        """
        Broadcast LED state change to all connected clients.
        
        Args:
            team_id: ID of the team whose LED state changed
            led_state: New state of the LED (True = on, False = off)
        """
        try:
            self.socketio.emit('led_state_changed', {
                'team_id': team_id,
                'led_state': led_state
            })
            logger.debug(f"Broadcasted led_state_changed event for team {team_id}: {led_state}")
        except Exception as e:
            logger.error(f"Error broadcasting led_state_changed event: {str(e)}")
    
    def broadcast_led_flashing(self, team_id: str, duration: float) -> None:
        """
        Broadcast LED flashing notification to all connected clients.
        
        Args:
            team_id: ID of the team whose LED is flashing
            duration: Duration of the flash in seconds
        """
        try:
            self.socketio.emit('led_flashing', {
                'team_id': team_id,
                'duration': duration
            })
            logger.debug(f"Broadcasted led_flashing event for team {team_id}: {duration}s")
        except Exception as e:
            logger.error(f"Error broadcasting led_flashing event: {str(e)}")
    
    def broadcast_latch_reset(self, team_id: str) -> None:
        """
        Broadcast latch reset notification to all connected clients.
        
        Args:
            team_id: ID of the team whose latch was reset
        """
        try:
            self.socketio.emit('latch_reset', {'team_id': team_id})
            logger.debug(f"Broadcasted latch_reset event for team: {team_id}")
        except Exception as e:
            logger.error(f"Error broadcasting latch_reset event: {str(e)}")
