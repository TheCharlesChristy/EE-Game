from EEGame.app.server.Teams.team import Team
from EEGame.app.server.Teams.pin import Pin
from typing import Dict, Any, Optional

class TeamManager:
    """
    TeamManager Class - Multi-Team Gaming System
    =================================
    A class to manage teams in the Multi-Team Gaming System.
    This class provides methods to create, update, and retrieve team information.
    """

    def __init__(self):
        """
        Initialize the TeamManager class.
        """
        self.teams: Dict[str, Team] = {}  # Dictionary to store teams by team_id
 

    def create_team(self, team_id: str, name: str, team_color: str, latch_pin: int, reset_pin: int, led_pin: int) -> Team:
        """
        Create a new team and add it to the manager.
        
        Args:
            team_id: Unique identifier for the team.
            name: Name of the team.
            team_color: Color of the team.
            latch_pin: GPIO pin number for the latch pin.
            reset_pin: GPIO pin number for the reset pin.
            led_pin: GPIO pin number for the LED pin.
        
        Returns:
            Team: The created team object.
        """
        if team_id in self.teams:
            raise ValueError(f"Team with ID {team_id} already exists.")
        
        team = Team(team_id, name, team_color, latch_pin, reset_pin, led_pin)
        self.teams[team_id] = team
        return team
    
    def update_team(self, team_id: str, name: Optional[str] = None, team_color: Optional[str] = None,
                   latch_pin: Optional[int] = None, reset_pin: Optional[int] = None, led_pin: Optional[int] = None) -> Team:
        """
        Update an existing team's information.
        
        Args:
            team_id: Unique identifier for the team.
            name: New name for the team (optional).
            team_color: New color for the team (optional).
            latch_pin: New GPIO pin number for the latch pin (optional).
            reset_pin: New GPIO pin number for the reset pin (optional).
            led_pin: New GPIO pin number for the LED pin (optional).
        
        Returns:
            Team: The updated team object.
        """
        if team_id not in self.teams:
            raise ValueError(f"Team with ID {team_id} does not exist.")
        
        team = self.teams[team_id]
        if name is not None:
            team.name = name
        if team_color is not None:
            team.team_color = team_color
        if latch_pin is not None:
            team.update_pins(latch_pin=latch_pin)
        if reset_pin is not None:
            team.update_pins(reset_pin=reset_pin)
        if led_pin is not None:
            team.update_pins(led_pin=led_pin)
        
        return team

    def get_team(self, team_id: str) -> Optional[Team]:
        """
        Retrieve a team by its ID.
        
        Args:
            team_id: Unique identifier for the team.
        
        Returns:
            Team: The team object if found, otherwise None.
        """
        return self.teams.get(team_id)
    
    def get_all_teams(self) -> Dict[str, Team]:
        """
        Retrieve all teams managed by the TeamManager.
        
        Returns:
            Dict[str, Team]: Dictionary of all teams with team_id as keys.
        """
        return self.teams
    
    def remove_team(self, team_id: str) -> None:
        """
        Remove a team from the manager.
        
        Args:
            team_id: Unique identifier for the team to be removed.
        
        Raises:
            ValueError: If the team does not exist.
        """
        if team_id not in self.teams:
            raise ValueError(f"Team with ID {team_id} does not exist.")
        
        # Close the pins before removing the team
        team = self.teams[team_id]
        team.close()

        # Remove the team from the dictionary        
        del self.teams[team_id]
