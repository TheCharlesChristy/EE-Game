"""Global Python types for the server application."""

from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from pathlib import Path
        
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
