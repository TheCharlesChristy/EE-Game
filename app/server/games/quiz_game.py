"""
Quiz Game - Multi-Team Gaming System
====================================

A competitive quiz game where teams buzz in to answer questions.
The first team to buzz gets to answer. Correct answers earn points,
wrong answers lock the team out for that question.

Author: Multi-Team Gaming System Development Team
Version: 1.0.0 MVP
"""

from EEGame.app.server.games.game_base import GameBase
from EEGame.app.server.services.data_service import DataService
from EEGame.app.server.services.team_manager import TeamManager
from flask_socketio import SocketIO
import time
import threading
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class QuizGameState(Enum):
    """Enum for quiz game states"""
    WAITING = "waiting"
    QUESTION_DISPLAY = "question_display"
    ACCEPTING_BUZZES = "accepting_buzzes"
    TEAM_ANSWERING = "team_answering"
    ANSWER_RESULT = "answer_result"
    GAME_OVER = "game_over"


@dataclass
class QuizTeamData:
    """Data class for team information in quiz game"""
    team_id: str
    name: str
    score: int = 0
    locked_out: bool = False
    has_buzzed: bool = False
    buzzer_timestamp: Optional[float] = None


class QuizGame(GameBase):
    """
    Quiz Game Class - Multi-Team Gaming System
    ==========================================
    
    A buzzer-based quiz competition where teams compete to answer questions.
    
    Game Flow:
    1. Game runner presses start
    2. Question appears on screen
    3. Contestants press their latch to buzz in
    4. First buzzer pauses the game for that team to answer
    5. Game runner marks answer as correct/incorrect
    6. Correct: Award points, next question
    7. Incorrect: Lock team out, continue with other teams
    8. If all teams wrong or locked out, skip to next question
    9. Game ends after 15 questions answered
    """
    
    def __init__(self, socketio: SocketIO, data_service: DataService, team_manager: TeamManager):
        """Initialize the Quiz Game"""
        super().__init__(socketio, data_service, team_manager, "QuizGame", socketio_base_event="quiz/")
        
        # Game configuration
        self.total_questions = 15
        self.questions_answered = 0
        self.current_question = None
        self.current_question_index = 0
        
        # Game state
        self.game_state = QuizGameState.WAITING
        self.teams: Dict[str, QuizTeamData] = {}
        self.current_answering_team: Optional[str] = None
        self.buzzer_order: List[str] = []
        self.answered_questions: Set[int] = set()
        
        # Threading
        self.state_lock = threading.Lock()
        self.buzzer_enabled = False
        
        self.logger.info("Quiz Game initialized")
    
    def initialize_teams(self) -> None:
        """Initialize team data for the quiz game"""
        teams = self.team_manager.get_all_teams()
        self.teams = {}
        
        for team_id, team in teams.items():
            self.teams[team_id] = QuizTeamData(
                team_id=team_id,
                name=team.name,
                score=0,
                locked_out=False,
                has_buzzed=False,
                buzzer_timestamp=None
            )
        
        self.logger.info(f"Initialized {len(self.teams)} teams for quiz game")
    
    def emit_team_scores(self) -> None:
        """Emit current team scores to all clients"""
        scores = {
            team_id: {
                "name": team_data.name,
                "score": team_data.score,
                "locked_out": team_data.locked_out,
                "has_buzzed": team_data.has_buzzed
            }
            for team_id, team_data in self.teams.items()
        }
        self.emit_to_all("team_scores", {"scores": scores})
    
    def emit_game_state(self) -> None:
        """Emit current game state to all clients"""
        state_data = {
            "state": self.game_state.value,
            "questions_answered": self.questions_answered,
            "total_questions": self.total_questions,
            "current_answering_team": self.current_answering_team,
            "buzzer_enabled": self.buzzer_enabled
        }
        
        if self.current_question:
            state_data["current_question"] = {
                "question": self.current_question.question,
                "points": self.current_question.points,
                "type": self.current_question.type
            }
        
        self.emit_to_all("game_state", state_data)
    
    def get_next_question(self) -> Optional[Any]:
        """Get the next random question that hasn't been asked"""
        try:
            # Get a random question from all available sets
            question = self.data_service.get_random_question_from_all_sets()
            return question
        except Exception as e:
            self.logger.error(f"Error getting next question: {e}")
            return None
    
    def reset_team_states_for_question(self) -> None:
        """Reset team states for a new question"""
        with self.state_lock:
            for team_data in self.teams.values():
                team_data.locked_out = False
                team_data.has_buzzed = False
                team_data.buzzer_timestamp = None
            self.buzzer_order = []
            self.current_answering_team = None
    
    def handle_team_buzzer(self, team_id: str) -> None:
        """Handle a team buzzing in"""
        with self.state_lock:
            # Check if buzzer is enabled and team can buzz
            if not self.buzzer_enabled:
                self.logger.debug(f"Team {team_id} buzzed but buzzer not enabled")
                return
            
            if team_id not in self.teams:
                self.logger.warning(f"Unknown team {team_id} attempted to buzz")
                return
            
            team_data = self.teams[team_id]
            
            # Check if team is locked out or has already buzzed
            if team_data.locked_out or team_data.has_buzzed:
                self.logger.debug(f"Team {team_id} cannot buzz (locked_out={team_data.locked_out}, has_buzzed={team_data.has_buzzed})")
                return
            
            # Record the buzz
            team_data.has_buzzed = True
            team_data.buzzer_timestamp = time.time()
            self.buzzer_order.append(team_id)
            
            # If this is the first buzz, pause the game
            if len(self.buzzer_order) == 1:
                self.buzzer_enabled = False
                self.current_answering_team = team_id
                self.game_state = QuizGameState.TEAM_ANSWERING
                
                self.logger.info(f"Team {team_id} buzzed in first!")
                
                # Emit buzzer event
                self.emit_to_all("team_buzzed", {
                    "team_id": team_id,
                    "team_name": team_data.name,
                    "is_first": True
                })
                
                # Update game state
                self.emit_game_state()
                self.emit_team_scores()
    
    def mark_answer(self, correct: bool) -> None:
        """Mark the current team's answer as correct or incorrect"""
        with self.state_lock:
            if not self.current_answering_team or self.game_state != QuizGameState.TEAM_ANSWERING:
                self.logger.warning("No team currently answering")
                return
            
            team_data = self.teams[self.current_answering_team]
            
            if correct:
                # Award points
                points = self.current_question.points if self.current_question else 10
                team_data.score += points
                
                self.logger.info(f"Team {self.current_answering_team} answered correctly! +{points} points")
                
                # Emit correct answer event
                self.emit_to_all("answer_result", {
                    "team_id": self.current_answering_team,
                    "team_name": team_data.name,
                    "correct": True,
                    "points_awarded": points,
                    "new_score": team_data.score
                })
                
                # Move to next question after a delay
                self.game_state = QuizGameState.ANSWER_RESULT
                self.emit_game_state()
                self.emit_team_scores()
                
                # Schedule next question
                threading.Timer(3.0, self.next_question).start()
                
            else:
                # Lock out the team
                team_data.locked_out = True
                
                self.logger.info(f"Team {self.current_answering_team} answered incorrectly")
                
                # Emit incorrect answer event
                self.emit_to_all("answer_result", {
                    "team_id": self.current_answering_team,
                    "team_name": team_data.name,
                    "correct": False,
                    "points_awarded": 0,
                    "new_score": team_data.score
                })
                
                # Check if any teams can still answer
                active_teams = [t for t in self.teams.values() if not t.locked_out]
                
                if active_teams:
                    # Resume accepting buzzes
                    self.current_answering_team = None
                    self.game_state = QuizGameState.ACCEPTING_BUZZES
                    self.buzzer_enabled = True
                    
                    self.emit_to_all("resume_buzzing", {
                        "message": "Incorrect! Other teams may now buzz in.",
                        "active_teams": len(active_teams)
                    })
                else:
                    # All teams locked out, skip question
                    self.emit_to_all("question_skipped", {
                        "message": "All teams have answered incorrectly. Moving to next question."
                    })
                    
                    # Move to next question after a delay
                    self.game_state = QuizGameState.ANSWER_RESULT
                    threading.Timer(3.0, self.next_question).start()
                
                self.emit_game_state()
                self.emit_team_scores()
    
    def skip_question(self) -> None:
        """Skip the current question without counting it"""
        with self.state_lock:
            if self.game_state in [QuizGameState.WAITING, QuizGameState.GAME_OVER]:
                self.logger.warning("Cannot skip question in current state")
                return
            
            self.logger.info("Skipping current question")
            
            # Emit skip event
            self.emit_to_all("question_skipped", {
                "message": "Question skipped by game runner.",
                "manual_skip": True
            })
            
            # Reset states and move to next question
            self.reset_team_states_for_question()
            self.game_state = QuizGameState.QUESTION_DISPLAY
            
            # Don't increment questions_answered for skips
            self.display_next_question()
    
    def next_question(self) -> None:
        """Move to the next question"""
        with self.state_lock:
            # Increment questions answered
            self.questions_answered += 1
            
            # Check if game is over
            if self.questions_answered >= self.total_questions:
                self.end_game()
                return
            
            # Reset team states
            self.reset_team_states_for_question()
            
            # Move to question display state
            self.game_state = QuizGameState.QUESTION_DISPLAY
            
        # Display the next question
        self.display_next_question()
    
    def display_next_question(self) -> None:
        """Display the next question to all players"""
        # Get next question
        self.current_question = self.get_next_question()
        
        if not self.current_question:
            self.logger.error("No questions available!")
            self.emit_to_all("error", {"message": "No questions available. Please check question files."})
            self.stop_game()
            return
        
        self.current_question_index += 1
        
        with self.state_lock:
            # Display question
            self.game_state = QuizGameState.QUESTION_DISPLAY
            
            self.emit_to_all("new_question", {
                "question_number": self.questions_answered + 1,
                "total_questions": self.total_questions,
                "question": self.current_question.question,
                "points": self.current_question.points,
                "type": self.current_question.type
            })
            
            self.emit_game_state()
            
            # After a delay, enable buzzers
            threading.Timer(2.0, self.enable_buzzers).start()
    
    def enable_buzzers(self) -> None:
        """Enable buzzers for teams to answer"""
        with self.state_lock:
            if self.game_state != QuizGameState.QUESTION_DISPLAY:
                return
            
            self.game_state = QuizGameState.ACCEPTING_BUZZES
            self.buzzer_enabled = True
            
            self.emit_to_all("buzzers_enabled", {
                "message": "Buzzers are now active!"
            })
            
            self.emit_game_state()
    
    def end_game(self) -> None:
        """End the game and determine winner"""
        with self.state_lock:
            self.game_state = QuizGameState.GAME_OVER
            self.buzzer_enabled = False
            
            # Determine winner(s)
            if self.teams:
                max_score = max(team.score for team in self.teams.values())
                winners = [team for team in self.teams.values() if team.score == max_score]
                
                winner_data = {
                    "winners": [
                        {"team_id": w.team_id, "name": w.name, "score": w.score} 
                        for w in winners
                    ],
                    "all_scores": [
                        {"team_id": t.team_id, "name": t.name, "score": t.score}
                        for t in sorted(self.teams.values(), key=lambda x: x.score, reverse=True)
                    ]
                }
                
                self.emit_to_all("game_over", winner_data)
                self.logger.info(f"Game over! Winners: {[w.name for w in winners]}")
            else:
                self.emit_to_all("game_over", {"message": "Game over - no teams participated"})
            
            self.emit_game_state()
            self.emit_team_scores()
    
    def latch_callback(self, team_id: str, timestamp: float) -> None:
        """Handle team button press from hardware"""
        self.logger.debug(f"Team {team_id} pressed button at {timestamp}")
        
        # Only handle buzzer if game is accepting buzzes
        if self.game_state == QuizGameState.ACCEPTING_BUZZES and self.buzzer_enabled:
            self.handle_team_buzzer(team_id)
    
    def set_team_callbacks(self) -> None:
        """Set callbacks for all team latches"""
        teams = self.team_manager.get_all_teams()
        
        for team_id, team in teams.items():
            # Set the callback
            team.set_callback(
                lambda tid=team_id, ts=time.time(): self.latch_callback(tid, ts)
            )
            
            # Reset the latch to ensure it's ready
            team.reset_latch()
        
        self.logger.info(f"Set callbacks for {len(teams)} teams")
    
    def game_loop(self) -> None:
        """Main game loop"""
        # Initialize teams
        self.initialize_teams()
        
        # Emit initial state
        self.emit_team_scores()
        self.emit_game_state()
        
        # Set team callbacks
        self.set_team_callbacks()
        
        self.logger.info("Starting Quiz Game")
        self.game_active = True
        
        # Start with first question
        self.display_next_question()
        
        # Game loop continues via callbacks and timers
        while self.game_active and self.game_state != QuizGameState.GAME_OVER:
            time.sleep(0.1)
        
        self.logger.info("Quiz Game ended")

    def run(self):
        self.game_loop()
    
    def stop_game(self) -> None:
        """Stop the game"""
        super().stop_game()
        
        with self.state_lock:
            self.buzzer_enabled = False
            self.game_state = QuizGameState.WAITING
            
        self.emit_to_all("game_stopped", {"message": "Quiz game has been stopped"})