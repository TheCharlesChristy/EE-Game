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
        print("INITIALIZING REACTION TIMER GAME")
        print(socketio)
        super().__init__(socketio, data_service, team_manager, "ReactionTimerGame", socketio_base_event="reaction/")

        # Set default times for the game
        self.set_default_times(time_to_green=2.0, time_in_green=1.0, percentage_deviation=0.2)

        self.screen_state = "red"
        self.round_number = 0

        self.players: Dict[str, Any] = self.generate_initial_player_data()

    def set_default_times(self, time_to_green: float = 2.0, time_in_green: float = 1.0, percentage_deviation: float = 0.2) -> None:
        """
        Set the default times for the game.
        
        Args:
            time_to_green (float): Average time to wait before changing to green.
            time_in_green (float): Average time to wait in green before changing back to red.
            percentage_deviation (float): Percentage deviation from the average times.
        """
        self.time_to_green = time_to_green
        self.time_in_green = time_in_green
        self.percentage_deviation = percentage_deviation
        self.logger.info(f"Default times set: {self.time_to_green}s to green, {self.time_in_green}s in green, {self.percentage_deviation*100}% deviation")

    def generate_initial_player_data(self) -> Dict[str, Any]:
        """
        Generate initial player data for the game.
        
        Returns:
            Dict[str, Any]: Dictionary containing initial player data.
        """
        teams = self.team_manager.get_all_teams()
        self.players = {}
        for team_id, team in teams.items():
            # Initialize each team with 3 lives and an empty set for completed rounds
            self.players[team_id] = {
                "lives": 3,
                "rounds_completed": set()
            }
        return self.players

    def lose_life(self, team_id: str) -> None:
        """
        Decrease the life count for a team.
        
        Args:
            team_id (str): Unique identifier for the team.
        """
        if team_id in self.players:
            self.players[team_id]["lives"] -= 1

            self.logger.info(f"Team {team_id} lost a life. Lives left: {self.players[team_id]['lives']}")

            # Emit team update
            team = self.team_manager.get_team(team_id)
            self.emit_to_all("team_update", {
                "team_id": team_id,
                "name": team.name if team else f"Team {team_id}",
                "lives": self.players[team_id]["lives"],
                "status": "active" if self.players[team_id]["lives"] > 0 else "eliminated"
            })

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

        # Check if the game is active
        if not self.game_active:
            self.logger.info(f"Game is not active. Team {team_id} cannot react.")
            return
        
        # Check if the team exists or is alive
        if team_id not in self.players or self.players[team_id]["lives"] <= 0:
            self.logger.info(f"Team {team_id} is not active or has no lives left. Ignoring reaction.")
            return

        # If the screen is red then they lose a life
        if self.screen_state == "red":
            # Show "too early" message
            self.emit_to_all("screen_state", {"state": "too_early", "message": "TOO EARLY!"})
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

        # Reset the latch pin for the team
        team.reset_latch()

    def show_red_screen(self):
        """
        Show the red screen for a random duration.
        """
        self.screen_state = "red"
        self.logger.info("Emitting red screen (wait state) to all clients")
        self.emit_to_all("screen_state", {"state": "wait", "message": "WAIT..."})
        self.logger.info("Red screen emission complete")

    def show_green_screen(self):
        """
        Show the green screen for a random duration.
        """
        self.screen_state = "green"
        self.logger.info("Emitting green screen (go state) to all clients")
        self.emit_to_all("screen_state", {"state": "go", "message": "GO!"})
        self.logger.info("Green screen emission complete")

    def emit_all_team_data(self):
        """
        Emit the current state of all teams to all connected clients.
        This method is used to update the UI with the latest team data.
        """
        team_data = {}
        teams = self.team_manager.get_all_teams()
        
        for team_id, team in teams.items():
            if team_id in self.players:
                team_data[team_id] = {
                    "name": team.name,
                    "lives": self.players[team_id]["lives"],
                    "status": "active" if self.players[team_id]["lives"] > 0 else "eliminated",
                    "rounds_completed": list(self.players[team_id]["rounds_completed"])
                }
            else:
                team_data[team_id] = {
                    "name": team.name,
                    "lives": 0,
                    "status": "eliminated",
                    "rounds_completed": []
                }

        self.emit_to_all("team_data", team_data)

    def decrease_times(self) -> None:
        self.time_to_green *= 0.9
        self.time_in_green *= 0.9
        self.percentage_deviation *= 1.1


    def run(self):
        """
        Main game loop for the Reaction Timer Game.
        This method will be run in a separate thread when the game starts.
        """
        # Get all the teams
        teams = self.team_manager.get_all_teams()
        self.logger.info(f"Teams available: {list(teams.keys())}")

        # Create a mapping between team ids and their lives
        self.players = self.generate_initial_player_data()
        self.logger.info(f"Generated player data: {self.players}")

        self.logger.info(f"Starting {self.game_name} game with teams: {list(self.players.keys())}")

        self.game_active = True
        self.round_number = 0

        # Emit initial team data
        self.emit_all_team_data()

        # Set the callbacks for each team's latch pin
        self.set_team_callbacks()

        # Set initial screen state
        self.emit_to_all("screen_state", {"state": "neutral", "message": "GET READY"})

        while self.game_active:
            # Set the screen to red
            self.logger.info("Setting screen to RED (wait state)")
            self.show_red_screen()

            # Wait for a random time before changing to green
            wait_time = self.time_to_green * (1 + random.uniform(-self.percentage_deviation, self.percentage_deviation))
            time.sleep(wait_time)

            # Check if game is still active (could have been stopped)
            if not self.game_active:
                break

            # Set the screen to green
            self.show_green_screen()

            # Wait for a random time before changing back to red
            wait_time = self.time_in_green * (1 + random.uniform(-self.percentage_deviation, self.percentage_deviation))
            time.sleep(wait_time)

            # Check if game is still active
            if not self.game_active:
                self.logger.info("Game stopped during green phase")
                break

            # Show results screen briefly
            self.emit_to_all("screen_state", {"state": "results", "message": f"ROUND {self.round_number} COMPLETE"})
            time.sleep(1)

            # Find the teams that have not completed this round if any
            teams_not_completed = [team_id for team_id, data in self.players.items() if self.round_number not in data["rounds_completed"]]

            # If there are teams that have not completed this round, they lose a life
            if teams_not_completed:
                for team_id in teams_not_completed:
                    self.lose_life(team_id)

            # Increment the round number
            self.round_number += 1
            self.logger.info(f"Round {self.round_number} completed")

            # Check if any teams are left
            if len(self.players) == 0 or len(self.players) == 1:
                break
    
        self.logger.info(f"{self.game_name} game has ended.")
        self.emit_to_all("screen_state", {"state": "neutral", "message": "GAME OVER"})
        self.emit_to_all("game_over", {"message": "The game has ended."})
        self.stop_game()

    def get_team_data(self) -> Dict[str, Any]:
        """
        Get the current state of all teams.
        
        Returns:
            Dict[str, Any]: Dictionary containing team data.
        """
        return {team_id: {"lives": data["lives"], "rounds_completed": list(data["rounds_completed"])} for team_id, data in self.players.items()}

    def stop_game(self):
        """
        Stop the game and reset the screen state.
        """
        self.game_active = False
        self.emit_to_all("screen_state", {"state": "neutral", "message": "GAME STOPPED"})
        super().stop_game()

    def start_game(self):
        """
        Start the game and emit initial team data.
        """
        self.players = self.generate_initial_player_data()
        self.emit_all_team_data()
        super().start_game()