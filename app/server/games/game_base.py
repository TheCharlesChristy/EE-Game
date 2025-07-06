"""
GameBase Class - Multi-Team Gaming System
=========================================

A base class that other game classes will inherit from. This class provides:
1. Flask SocketIO interface for real-time communication with clients
2. Logger attribute for consistent logging across all games
3. GPIO service attribute for hardware interaction
4. Data service attribute for accessing question sets and game data

Author: Multi-Team Gaming System Development Team
Version: 1.0.0
"""

import logging
from typing import Optional, Dict, Any
from flask_socketio import SocketIO, emit
from abc import ABC, abstractmethod

from EEGame.app.server.services.data_service import DataService
from EEGame.app.server.services.team_manager import TeamManager
from EEGame.app.server.EElogging import setup_logging
import threading


class GameBase(ABC):
    """
    Base class for all game implementations in the Multi-Team Gaming System.
    
    This class provides common functionality needed by all games:
    - SocketIO interface for real-time communication
    - Logging capabilities
    - GPIO service for hardware interaction
    - Data service for accessing questions and configuration
    """
    
    def __init__(self, 
                 socketio: SocketIO, 
                 data_service: DataService,
                 team_manager: TeamManager,
                 game_name: str = "BaseGame"):
        """
        Initialize the GameBase class.
        
        Args:
            socketio: Flask-SocketIO instance for real-time communication
            data_service: Data service for accessing questions and configuration
            game_name: Name of the game (used for logging)
        """
        # Set up logging
        setup_logging()
        self.logger = logging.getLogger(f"{__name__}.{game_name}")
        
        # Store service references
        self.socketio = socketio
        self.data_service = data_service
        self.team_manager = team_manager
        
        # Game state
        self.game_name = game_name
        self.game_thread: Optional[threading.Thread] = None
        
        self.logger.info(f"Initialized {game_name} game")
    
    # SocketIO Interface Methods
    def emit_to_all(self, event: str, data: Dict[str, Any] = None, namespace: str = None):
        """
        Emit an event to all connected clients.
        
        Args:
            event: Event name to emit
            data: Data to send with the event
            namespace: Optional namespace to emit to
        """
        try:
            self.socketio.emit(event, data or {}, namespace=namespace)
            self.logger.debug(f"Emitted '{event}' to all clients: {data}")
        except Exception as e:
            self.logger.error(f"Failed to emit '{event}' to all clients: {e}")
    
    def emit_to_room(self, room: str, event: str, data: Dict[str, Any] = None, namespace: str = None):
        """
        Emit an event to a specific room.
        
        Args:
            room: Room name to emit to
            event: Event name to emit
            data: Data to send with the event
            namespace: Optional namespace to emit to
        """
        try:
            self.socketio.emit(event, data or {}, room=room, namespace=namespace)
            self.logger.debug(f"Emitted '{event}' to room '{room}': {data}")
        except Exception as e:
            self.logger.error(f"Failed to emit '{event}' to room '{room}': {e}")

    @abstractmethod
    def latch_callback(self, team_id: str):
        """
        Abstract method to handle latch pin callback.
        
        This method should be implemented by subclasses to define the behavior
        when a latch pin is pressed for a specific team.
        
        Args:
            team_id: Unique identifier for the team that triggered the latch
            data: Additional data related to the latch event
        """
        pass

    @abstractmethod
    def run(self):
        """
        Abstract method to run the game logic.
        
        This method should be implemented by subclasses to define the game flow.
        """
        pass

    def start_game(self):
        """
        Start the game. Running the game logic in a separate thread.
        
        This method should be called to initialize and start the game logic.
        """
        # Check if the game thread is already running if so then kill it
        if self.game_thread and self.game_thread.is_alive():
            self.logger.warning(f"Game thread for {self.game_name} is already running. Stopping it before starting a new one.")
            self.game_thread.join(timeout=1)

        # Create a new thread for the game logic
        self.game_thread = threading.Thread(target=self.run)
        self.game_thread.start()
        self.logger.info(f"Started {self.game_name} game in a new thread")

    def stop_game(self):
        """
        Stop the game.
        
        This method should be called to stop the game logic and clean up resources.
        """
        if self.game_thread and self.game_thread.is_alive():
            self.logger.info(f"Stopping {self.game_name} game")
            self.game_thread.join(timeout=1)
            self.logger.info(f"{self.game_name} game stopped")
        else:
            self.logger.warning(f"{self.game_name} game is not running or has already been stopped")
    
    # Utility Methods
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def log_info(self, message: str):
        """Log an info message."""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """Log an error message."""
        self.logger.error(message)
    
    def log_debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)