import logging
from flask_socketio import emit, SocketIO
from EEGame.app.server.services.team_manager import TeamManager
from EEGame.app.server.services.data_service import DataService
from EEGame.app.server.games.reaction_timer_game import ReactionTimerGame
from EEGame.app.server.EElogging import setup_logging

class GameService:
    """
    GameService class to handle game-related operations.
    This class is responsible for managing game state, teams, and player interactions.
    """

    def __init__(self, socketio: SocketIO, team_manager: TeamManager, data_service: DataService):
        self.team_manager = team_manager
        self.data_service = data_service
        setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("GameService initialized")

        self.reaction_game = ReactionTimerGame(
            socketio=socketio,
            data_service=self.data_service,
            team_manager=self.team_manager
        )

    def start_reaction_game(self):
        """
        Start the reaction timer game.
        """
        self.logger.info("Starting reaction timer game")
        self.reaction_game.start_game()

    def stop_reaction_game(self):
        """
        Stop the reaction timer game.
        """
        self.logger.info("Stopping reaction timer game")
        self.reaction_game.stop_game()