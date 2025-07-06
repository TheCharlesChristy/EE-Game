from EEGame.app.server.games.game_base import GameBase
from EEGame.app.server.services.data_service import DataService
from EEGame.app.server.services.team_manager import TeamManager
from flask_socketio import SocketIO
import time
import random
from typing import Dict, Any

class ReactionTimerGame(GameBase):
    """
    Reaction Timer Game Class - Multi-Team Gaming System
    ====================================================
    
    A game where players must react to a signal as quickly as possible.
    The game measures the time taken for each player to respond.
    
    Attributes:
        game_name (str): Name of the game.
        players (Dict[str, Any]): Dictionary to store player data.
        game_active (bool): Flag to indicate if the game is currently active.
    """
    
    def __init__(self, socketio: SocketIO, data_service: DataService, team_manager: TeamManager):
        super().__init__(socketio, data_service, team_manager, "ReactionTimerGame")

        self.time_to_green = 1.0 # Avg time to wait between start of red and start of green
        self.time_in_green = 0.5 # Avg time to wait in green before going back to red
        self.percentage_deviation = 0.2 # Percentage deviation from the average time to wait

        self.screen_state = "red"
        self.round_number = 0

        self.players: Dict[str, Any] = {}  # Dictionary to store player data

    def lose_life(self, team_id: str) -> None:
        """
        Decrease the life count for a team.
        
        Args:
            team_id (str): Unique identifier for the team.
        """
        if team_id in self.players:
            self.players[team_id]["lives"] -= 1

            self.logger.info(f"Team {team_id} lost a life. Lives left: {self.players[team_id]['lives']}")

            if self.players[team_id]["lives"] <= 0:
                # Remove the team from the game
                del self.players[team_id]

                # If there are no players left, end the game
                if len(self.players) == 0:
                    self.emit_to_all("game_over", {"message": "All teams have lost all their lives. Game Over!"})
                    self.logger.info("All teams have lost all their lives. Game Over!")
                    self.game_active = False
                    self.stop_game()
                else:
                    # Emit the team out event to all teams
                    self.emit_to_all("team_out", {"team_id": team_id, "message": f"Team {team_id} has lost all their lives."})
                    self.logger.info(f"Team {team_id} has lost all their lives and is out of the game.")

            else:
                # Emit the life lost event to the team
                self.emit_to_all("life_lost", {"team_id": team_id, "lives_left": self.players[team_id]["lives"]})
                

    def latch_callback(self, team_id: str) -> None:
        team = self.team_manager.get_team(team_id)

        # Reset the latch pin for the team
        team.reset_latch()

        # If the screen is red then they lose a life
        if self.screen_state == "red":
            self.lose_life(team_id)
            return

        # If the screen is green then they are safe for the round
        if self.screen_state == "green":
            # Check if the team has already completed this round
            if self.round_number in self.players[team_id]["rounds_completed"]:
                self.logger.info(f"Team {team_id} has already completed round {self.round_number}. Ignoring duplicate reaction.")
                return
            
            # Mark the round as completed for the team
            self.players[team_id]["rounds_completed"].add(self.round_number)

            # Emit the reaction event to all teams
            self.emit_to_all("reaction", {"team_id": team_id, "round": self.round_number})
            self.logger.info(f"Team {team_id} reacted in round {self.round_number}.")

    def show_red_screen(self):
        """
        Show the red screen for a random duration.
        """
        self.screen_state = "red"
        self.emit_to_all("screen_update", {"state": "red"})
        self.logger.info("Showing red screen")

    def show_green_screen(self):
        """
        Show the green screen for a random duration.
        """
        self.screen_state = "green"
        self.emit_to_all("screen_update", {"state": "green"})
        self.logger.info("Showing green screen")

    def run(self):
        """
        Main game loop for the Reaction Timer Game.
        This method will be run in a separate thread when the game starts.
        """
        # Get all the teams
        teams = self.team_manager.get_all_teams()

        # Create a mapping between team ids and their lives
        self.players = {team.team_id: {"lives": 5, "rounds_completed": set()} for team in teams}

        self.logger.info(f"Starting {self.game_name} game with teams: {list(self.players.keys())}")

        self.game_active = True
        self.round_number = 0

        while self.game_active:
            # Set the screen to red
            self.show_red_screen()

            # Wait for a random time before changing to green
            wait_time = self.time_to_green * (1 + random.uniform(-self.percentage_deviation, self.percentage_deviation))
            self.logger.info(f"Waiting for {wait_time:.2f} seconds before changing to green")
            time.sleep(wait_time)

            # Set the screen to green
            self.show_green_screen()

            # Wait for a random time before changing back to red
            wait_time = self.time_in_green * (1 + random.uniform(-self.percentage_deviation, self.percentage_deviation))
            self.logger.info(f"Waiting for {wait_time:.2f} seconds before changing back to red")
            time.sleep(wait_time)

            # Increment the round number
            self.round_number += 1
            self.logger.info(f"Round {self.round_number} completed")

            # Find the teams that have not completed this round if any
            teams_not_completed = [team_id for team_id, data in self.players.items() if self.round_number not in data["rounds_completed"]]

            # If there are teams that have not completed this round, they lose a life
            if teams_not_completed:
                self.logger.info(f"Teams {teams_not_completed} did not complete round {self.round_number}. They will lose a life.")
                for team_id in teams_not_completed:
                    self.lose_life(team_id)
    
        self.logger.info(f"{self.game_name} game has ended.")
        self.emit_to_all("game_over", {"message": "The game has ended."})
        self.stop_game()