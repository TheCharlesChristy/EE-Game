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
from EEGame.app.server.EEtypes import Question, QuestionSet
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
        self.question_set = "all"  # Default to all sets
        self.question_type = "all"  # Default to all types
        
        # Game state
        self.game_state = QuizGameState.WAITING
        self.teams: Dict[str, QuizTeamData] = {}
        self.current_answering_team: Optional[str] = None
        self.buzzer_order: List[str] = []
        self.answered_questions: Set[int] = set()
        
        # Threading
        self.state_lock = threading.Lock()
        self.buzzer_enabled = False
        
        # Timer management
        self.active_timers = []
        self.question_timer = None
        
        self.logger.info("Quiz Game initialized")

    def create_timer(self, delay: float, function, *args, **kwargs) -> threading.Timer:
        """Create and track a timer"""
        timer = threading.Timer(delay, function, args, kwargs)
        self.active_timers.append(timer)
        timer.start()
        return timer
    
    def cancel_all_timers(self) -> None:
        """Cancel all active timers"""
        for timer in self.active_timers:
            if timer.is_alive():
                timer.cancel()
        self.active_timers.clear()
        
        if self.question_timer and self.question_timer.is_alive():
            self.question_timer.cancel()
            self.question_timer = None

    def set_question_set(self, question_set: str) -> None:
        """Set the question set for the quiz game"""
        if question_set in self.data_service.get_all_question_sets_names():
            self.question_set = question_set
            self.logger.info(f"Question set set to: {self.question_set}")
        else:
            self.logger.warning(f"Invalid question set: {question_set}. Using default 'all' set.")
            self.question_set = "all"

    def set_question_type(self, question_type: str) -> None:
        """Set the question type for the quiz game"""
        if question_type in self.data_service.get_all_question_types(self.question_set):
            self.question_type = question_type
            self.logger.info(f"Question type set to: {self.question_type}")
        else:
            self.logger.warning(f"Invalid question type: {question_type}. Using default 'all' type.")
            self.question_type = "all"
    
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
    
    def get_next_question(self) -> Question:
        """Get the next random question that hasn't been asked"""
        try:
            self.logger.info(f"Getting next question - Set: {self.question_set}, Type: {self.question_type}")
            
            # For now, just use the question set
            # TODO: Add type filtering when data service supports it
            if self.question_set == "all":
                question = self.data_service.get_random_question_from_all_sets()
            else:
                question = self.data_service.get_random_question(self.question_set)
            
            if question:
                self.logger.info(f"Got question: {question.question[:50]}...")
                # If we need to filter by type and the question doesn't match, try again
                # This is a temporary solution until data service supports type filtering
                if self.question_type != "all" and hasattr(question, 'type') and question.type != self.question_type:
                    self.logger.info(f"Question type {question.type} doesn't match filter {self.question_type}, trying again...")
                    # For now, just use it anyway to avoid infinite loops
                    # TODO: Implement proper type filtering
            else:
                self.logger.warning("No question returned from data service")
                
            return question
        except Exception as e:
            self.logger.error(f"Error getting next question: {e}", exc_info=True)
            return None

    
    def reset_team_states_for_question(self) -> None:
        """Reset team states for a new question
        
        NOTE: This method should be called while already holding the state_lock
        to avoid deadlocks. Do not acquire the lock inside this method.
        """
        # Remove the 'with self.state_lock:' - assume caller already has the lock
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
                
                # Store data for emission outside the lock
                buzz_data = {
                    "team_id": team_id,
                    "team_name": team_data.name,
                    "is_first": True
                }
                should_emit = True
            else:
                should_emit = False
        
        # Emit events outside the lock to avoid potential deadlocks
        if should_emit:
            # Emit buzzer event
            self.emit_to_all("team_buzzed", buzz_data)
            
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
                self.create_timer(3.0, self.next_question)
                
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
                    # All teams locked out - need to set proper state
                    self.game_state = QuizGameState.ANSWER_RESULT
                    
                    # Emit question skipped with the correct answer
                    self.emit_to_all("question_skipped", {
                        "message": "All teams have answered incorrectly. Moving to next question.",
                        "correct_answer": self.current_question.correct_answer if self.current_question else ""
                    })
                    
                    # Schedule next question with a delay to show the message
                    self.create_timer(3.0, self.next_question)
                
                self.emit_game_state()
                self.emit_team_scores()

    def skip_question(self) -> None:
        """Skip the current question"""
        self.logger.info("Skip question called")
        
        # Cancel any active timers
        if hasattr(self, 'question_timer') and self.question_timer:
            self.question_timer.cancel()
            self.question_timer = None
        
        with self.state_lock:
            # Check if we're in a valid state to skip
            if self.game_state in [QuizGameState.WAITING, QuizGameState.GAME_OVER]:
                self.logger.warning(f"Cannot skip question in state: {self.game_state}")
                return
                
            self.buzzer_enabled = False
            # Important: Set the state to allow next_question to proceed
            self.game_state = QuizGameState.ANSWER_RESULT
            
        self.emit_to_all("question_skipped", {
            "message": "Question skipped by game operator",
            "correct_answer": self.current_question.correct_answer if self.current_question else ""
        })
        
        self.logger.info("Creating timer for next question after skip")
        # Use create_timer to ensure the timer is tracked
        self.create_timer(2.0, self.next_question)
    
    
    def next_question(self) -> None:
        """Move to the next question"""
        self.logger.info(f"next_question called. Current state: {self.game_state}, Questions answered: {self.questions_answered}")
        
        try:
            with self.state_lock:
                # Increment questions answered
                self.questions_answered += 1
                self.logger.info(f"Incremented questions_answered to: {self.questions_answered}")
                
                # Check if game is over
                if self.questions_answered >= self.total_questions:
                    self.logger.info("Game ending - reached total questions")
                    # Can't call end_game here as it might also need the lock
                    # Set a flag and handle it outside the lock
                    should_end = True
                else:
                    should_end = False
                    
                    # Reset team states - this no longer tries to acquire the lock
                    self.logger.info("Resetting team states")
                    self.reset_team_states_for_question()
                    
                    # Move to question display state
                    self.game_state = QuizGameState.QUESTION_DISPLAY
                    self.logger.info(f"Set game state to: {self.game_state}")
            
            # Handle game end outside the lock
            if should_end:
                self.end_game()
                return
                
            # Display the next question
            self.logger.info("About to call display_next_question")
            self.display_next_question()
            self.logger.info("Returned from display_next_question")
            
        except Exception as e:
            self.logger.error(f"Error in next_question: {e}", exc_info=True)
            # Try to recover by ending the game
            self.end_game()
    
    def display_next_question(self) -> None:
        """Display the next question to all clients"""
        self.logger.info("display_next_question called")
        
        with self.state_lock:
            question = self.get_next_question()
            
            if not question:
                self.logger.error("No more questions available")
                self.end_game()
                return
            
            self.current_question = question
            self.current_question_index += 1
            
            # Reset team states for new question
            for team in self.teams.values():
                team.locked_out = False
                team.has_buzzed = False
                team.buzzer_timestamp = None
            
            # Update game state
            self.game_state = QuizGameState.QUESTION_DISPLAY
            self.buzzer_enabled = False
            
            # Emit the question with answer options
            self.emit_to_all("new_question", {
                "question": question.question,
                "options": question.potential_answers,  # Make sure this is included!
                "points": question.points,
                "question_number": self.questions_answered + 1,
                "total_questions": self.total_questions
            })

            # Emit the correct answer to a secret channel for the game runner
            self.emit_to_all("correct_answer", {
                "correct_answer": question.correct_answer,
                "question_number": self.questions_answered + 1
            })
            
            self.emit_game_state()
            
            # After a delay, enable buzzers
            self.create_timer(3.0, self.enable_buzzers)
    
    def enable_buzzers(self) -> None:
        """Enable buzzers for teams to answer"""
        with self.state_lock:
            if self.game_state != QuizGameState.QUESTION_DISPLAY:
                return
                
            self.game_state = QuizGameState.ACCEPTING_BUZZES
            self.buzzer_enabled = True
            
        self.emit_to_all("buzzers_enabled", {"message": "Buzzers are now active!"})
        self.emit_game_state()
        
        # Set a timeout for the question (30 seconds)
        self.question_timer = self.create_timer(30.0, self.question_timeout)

    def question_timeout(self) -> None:
        """Handle question timeout when no team buzzes in"""
        with self.state_lock:
            if self.game_state == QuizGameState.ACCEPTING_BUZZES:
                self.logger.info("Question timed out - no teams buzzed")
                
                # Cancel buzzer acceptance
                self.buzzer_enabled = False
                # Set proper state for transition
                self.game_state = QuizGameState.ANSWER_RESULT
                
                # Emit timeout event
                self.emit_to_all("question_timeout", {
                    "message": "Time's up! No team buzzed in.",
                    "correct_answer": self.current_question.correct_answer if self.current_question else ""
                })
                
                # Move to next question after a delay
                self.create_timer(3.0, self.next_question)
    
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
        self.logger.info("Stopping quiz game")
        
        # Cancel all timers first
        self.cancel_all_timers()
        
        # Call parent stop_game
        super().stop_game()
        
        with self.state_lock:
            self.buzzer_enabled = False
            self.game_state = QuizGameState.WAITING
            
        self.emit_to_all("game_stopped", {"message": "Quiz game has been stopped"})