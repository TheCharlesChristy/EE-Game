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

    ##################### Quiz Game Endpoints #####################

    @socketio.on('quiz/start_game')
    def start_quiz_game(data):
        """Handle the start quiz game event."""
        logger.info(f"Received quiz/start_game event with data: {data}")
        
        # Extract filter parameters from the data
        question_set = data.get('question_set', 'all')
        question_type = data.get('question_type', 'all')
        
        logger.info(f"Starting quiz with question_set: {question_set}, question_type: {question_type}")
        
        # Set the filters on the quiz game instance
        if game_service.quiz_game:
            game_service.quiz_game.set_question_set(question_set)
            game_service.quiz_game.set_question_type(question_type)
        
        # Start the game
        game_service.start_quiz_game()
        
        # Emit game started with filter information
        emit('quiz/game_started', {
            'message': 'Quiz game started',
            'question_set': question_set,
            'question_type': question_type
        }, broadcast=True)

    @socketio.on('quiz/stop_game')
    def stop_quiz_game(data):
        """Handle the stop quiz game event."""
        logger.info("Received quiz/stop_game event")
        game_service.stop_quiz_game()
        emit('quiz/game_stopped', {'message': 'Quiz game stopped'}, broadcast=True)

    @socketio.on('quiz/mark_answer')
    def mark_quiz_answer(data):
        """Handle marking an answer as correct or incorrect."""
        logger.info(f"Received quiz/mark_answer event: {data}")
        correct = data.get('correct', False)
        game_service.quiz_game.mark_answer(correct)

    @socketio.on('quiz/skip_question')
    def skip_quiz_question(data):
        """Handle skipping the current question."""
        logger.info("Received quiz/skip_question event")
        game_service.quiz_game.skip_question()

    @socketio.on('quiz/get_game_state')
    def get_quiz_game_state(data):
        """Handle request for current game state."""
        logger.info("Received quiz/get_game_state event")
        game_service.quiz_game.emit_game_state()
        game_service.quiz_game.emit_team_scores()

    @socketio.on('quiz/get_question_sets')
    def get_quiz_game_state(data):
        """Handle request for current game state."""
        logger.info("Received quiz/get_game_state event")
        question_sets = game_service.data_service.get_all_question_sets_names()
        emit('quiz/question_sets', {'question_sets': question_sets})

    @socketio.on('quiz/get_question_types')
    def get_quiz_game_state(data):
        """Handle request for current game state."""
        logger.info("Received quiz/get_game_state event")
        question_set = data.get('question_set', 'all')
        question_types = game_service.data_service.get_all_question_types(question_set)
        emit('quiz/question_types', {'question_types': question_types})