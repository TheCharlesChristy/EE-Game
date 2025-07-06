"""Global Python types for the server application."""

from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from pathlib import Path

board_to_bcm = {
    3: 2,   # BCM 2
    5: 3,   # BCM 3
    7: 4,   # BCM 4
    8: 14,  # BCM 14
    10: 15, # BCM 15
    11: 17, # BCM 17
    12: 18, # BCM 18
    13: 27, # BCM 27
    15: 22, # BCM 22
    16: 23, # BCM 23
    18: 24, # BCM 24
    19: 10, # BCM 10 (MOSI)
    21: 9,  # BCM 9 (MISO)
    22: 25, # BCM 25
    23: 11, # BCM 11 (SCLK)
    24: 8,   # BCM8 (CE0)
    26: 7,   # BCM7 (CE1)
    29: 5,   # BCM5
    31: 6,   # BCM6
    32: 12,  # BCM12
    33: 13,  # BCM13
    35: 19,  # BCM19
    36: 16,  # BCM16
    37: 26,  # BCM26
    38: 20,  # BCM20
    40: 21,  # BCM21
}

@dataclass
class Pin:
    """Represents a GPIO pin configuration."""
    pin_number: int
    mode: str = "input" # "input" or "output"
    board_pin: bool = False # True if using board pin numbering, False if using BCM numbering
    callback: Optional[callable] = None

    pull_up_down: Optional[str] = None # "up", "down", or None
    initial_value: Optional[bool] = None # True, False, or None

    def get_pin_number(self) -> int:
        """Get the pin number in BCM format."""
        if self.board_pin:
            return board_to_bcm.get(self.pin_number, self.pin_number)
        return self.pin_number
    

@dataclass
class TeamPins:
    """Represents the GPIO pins for a team."""
    latch_pin: Pin
    reset_pin: Pin
    led_pin: Pin


@dataclass
class Team:
    """Represents a team with its name and GPIO pins."""
    name: str
    pins: TeamPins

    def __post_init__(self):
        if not isinstance(self.pins, TeamPins):
            raise ValueError("pins must be an instance of TeamPins")
        if not self.name:
            raise ValueError("Team name cannot be empty")
        
@dataclass
class Question:
    """Represents a single question."""
    type: str
    question: str
    potential_answers: List[Dict[str, Any]]
    correct_answer: str
    points: int
    num_asked: int = 0

@dataclass
class QuestionSet:
    """Represents a set of questions."""
    name: str
    questions: List[Question]
