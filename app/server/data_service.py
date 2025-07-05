"""
Data Service - File I/O Operations for Multi-Team Gaming System
Handles team data, questions, and configuration storage
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class Team:
    """Simple team data structure."""
    id: int
    name: str
    pin_set: int
    color: str
    status: str = "disconnected"


class DataService:
    """Simple data service using JSON file storage."""
    
    def __init__(self):
        self.data_dir = Path('app', 'data')
        self.teams_file = self.data_dir / 'teams.json'
        self.questions_file = self.data_dir / 'questions.json'
        self.config_file = self.data_dir / 'config.json'
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize data files if they don't exist
        self.init_data_files()
    
    def init_data_files(self):
        """Initialize data files with default content if they don't exist."""
        
        # Teams file
        if not self.teams_file.exists():
            default_teams = {
                "teams": [],
                "next_team_id": 1
            }
            self.save_json(self.teams_file, default_teams)
        
        # Questions file
        if not self.questions_file.exists():
            default_questions = {
                "questions": [
                    {
                        "id": 1,
                        "question": "What is the capital of France?",
                        "answer": "Paris",
                        "difficulty": "easy",
                        "points": 10
                    },
                    {
                        "id": 2,
                        "question": "What is 2 + 2?",
                        "answer": "4",
                        "difficulty": "easy",
                        "points": 5
                    }
                ]
            }
            self.save_json(self.questions_file, default_questions)
        
        # Config file
        if not self.config_file.exists():
            default_config = {
                "max_teams": 8,
                "default_reaction_time_ms": 200,
                "gpio_enabled": True,
                "games": {
                    "reaction_timer": {"enabled": True, "lives_per_team": 3},
                    "wheel_game": {"enabled": True, "total_rounds": 10},
                    "quiz_game": {"enabled": True}
                },
                "pin_mapping": {
                    "1": {"latch": 11, "reset": 12, "led": 13},
                    "2": {"latch": 15, "reset": 16, "led": 18},
                    "3": {"latch": 19, "reset": 21, "led": 23},
                    "4": {"latch": 24, "reset": 26, "led": 29},
                    "5": {"latch": 31, "reset": 32, "led": 33},
                    "6": {"latch": 35, "reset": 36, "led": 37},
                    "7": {"latch": 38, "reset": 40, "led": 3},
                    "8": {"latch": 5, "reset": 7, "led": 8}
                }
            }
            self.save_json(self.config_file, default_config)
    
    def load_json(self, file_path):
        """Load JSON data from file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_json(self, file_path, data):
        """Save JSON data to file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving JSON to {file_path}: {e}")
            return False
    
    # Team Management
    def get_teams(self) -> List[Dict]:
        """Get all teams."""
        data = self.load_json(self.teams_file)
        return data.get('teams', [])
    
    def get_team_count(self) -> int:
        """Get number of registered teams."""
        return len(self.get_teams())
    
    def add_team(self, name: str, pin_set: int) -> Optional[Dict]:
        """Add a new team."""
        data = self.load_json(self.teams_file)
        
        # Check if pin set is already in use
        existing_teams = data.get('teams', [])
        for team in existing_teams:
            if team.get('pin_set') == pin_set:
                return None  # Pin set already in use
        
        # Check max teams limit
        config = self.load_json(self.config_file)
        max_teams = config.get('max_teams', 8)
        if len(existing_teams) >= max_teams:
            return None  # Too many teams
        
        # Get team colors (simple rotation)
        colors = ["#e53e3e", "#3182ce", "#38a169", "#d69e2e", 
                  "#805ad5", "#dd6b20", "#319795", "#e53e3e"]
        color = colors[len(existing_teams) % len(colors)]
        
        # Create new team
        team_id = data.get('next_team_id', 1)
        new_team = {
            "id": team_id,
            "name": name,
            "pin_set": pin_set,
            "color": color,
            "status": "connected"
        }
        
        # Update data
        data['teams'].append(new_team)
        data['next_team_id'] = team_id + 1
        
        if self.save_json(self.teams_file, data):
            return new_team
        return None
    
    def remove_team(self, team_id: int) -> bool:
        """Remove a team by ID."""
        data = self.load_json(self.teams_file)
        teams = data.get('teams', [])
        
        # Find and remove team
        for i, team in enumerate(teams):
            if team.get('id') == team_id:
                teams.pop(i)
                return self.save_json(self.teams_file, data)
        
        return False
    
    def get_team_by_id(self, team_id: int) -> Optional[Dict]:
        """Get team by ID."""
        teams = self.get_teams()
        for team in teams:
            if team.get('id') == team_id:
                return team
        return None
    
    # Questions Management
    def get_questions(self) -> List[Dict]:
        """Get all quiz questions."""
        data = self.load_json(self.questions_file)
        return data.get('questions', [])
    
    def get_random_question(self) -> Optional[Dict]:
        """Get a random question."""
        import random
        questions = self.get_questions()
        return random.choice(questions) if questions else None
    
    # Configuration Management
    def get_config(self) -> Dict:
        """Get system configuration."""
        return self.load_json(self.config_file)
    
    def get_game_config(self, game_id: str) -> Dict:
        """Get configuration for a specific game."""
        config = self.get_config()
        return config.get('games', {}).get(game_id, {})
    
    def is_game_enabled(self, game_id: str) -> bool:
        """Check if a game is enabled."""
        game_config = self.get_game_config(game_id)
        return game_config.get('enabled', False)


# Global service instance
data_service = DataService()
