import logging
from flask_socketio import emit
from EEGame.app.server.services.game_service import GameService
from EEGame.app.server.EElogging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def create_game_endpoints(app, socketio, game_service: GameService):
    """
    Create game-related endpoints for the Flask application.
    
    Args:
        app: Flask application instance
        socketio: SocketIO instance
        game_service: GameService instance to handle game logic
    """

    ##################### Reaction Game Endpoints #####################    
    @socketio.on('reaction/start_game')
    def start_reaction_game(data):
        """Handle the start game event."""
        logger.info("Received start_game event")
        game_service.start_reaction_game()
        emit('game_started', {'message': 'Reaction game started'}, broadcast=True)
    
    @socketio.on('reaction/stop_game')
    def stop_reaction_game(data):
        """Handle the stop game event."""
        logger.info("Received stop_game event")
        game_service.stop_reaction_game()
        emit('game_stopped', {'message': 'Reaction game stopped'}, broadcast=True)

    @socketio.on("reaction/get_team_data")
    def get_team_data(data):
        """Handle the request for team data."""
        logger.info("Received get_team_data event")
        game_service.reaction_game.emit_all_team_data()

    @socketio.on("reaction/test_screen_state")
    def test_screen_state(data):
        """Handle the test screen state event for debugging."""
        logger.info(f"Received test_screen_state event: {data}")
        state = data.get('state', 'neutral')
        message = data.get('message', 'TEST')
        game_service.reaction_game.emit_to_all("reaction/screen_state", {"state": state, "message": message})
        logger.info(f"Emitted test screen state: {state} - {message}")