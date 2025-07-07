"""Class that handles loading the data"""

import json
from pathlib import Path
from typing import Dict, Optional, List, Union
import random
from EEGame.app.server.EEtypes import Question, QuestionSet

class DataService:
    def __init__(self, data_dir: Union[str, Path]):
        """Initialize the DataService with the path to the data directory."""
        if isinstance(data_dir, str):
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = data_dir

        self.question_sets: Dict[str, QuestionSet] = {}
        self.load_question_sets()

    def load_question_sets(self) -> None:
        """Load all question sets from the data directory."""
        for file_path in self.data_dir.glob("*.json"):
            self.load_question_set(file_path)

    def load_question_set(self, file_path: Path) -> None:
        """Load a single question set from a JSON file."""
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            question_set = QuestionSet(
                name=file_path.stem, # Name of file without extension
                questions=[
                    Question(
                        type=q["type"],
                        question=q["question"],
                        potential_answers=q["answers"],
                        correct_answer=q["correct"],
                        points=q["points"]
                    ) for q in data["questions"]
                ]
            )
            self.question_sets[question_set.name] = question_set

    def get_question_set(self, name: str) -> Optional[QuestionSet]:
        """Get a question set by name."""
        return self.question_sets.get(name)
    
    def get_all_question_sets(self) -> List[QuestionSet]:
        """Get a list of all question sets."""
        return list(self.question_sets.values())
    
    def get_random_question(self, q_set: Union[str, QuestionSet]) -> Question:
        """Get a random question from a question set."""
        if isinstance(q_set, str):
            q_set = self.get_question_set(q_set)
        if not q_set or not q_set.questions:
            raise ValueError("Question set is empty or does not exist.")
        
        # Choose a random question preferring those that have not been asked yet
        unasked_questions = [q for q in q_set.questions if q.num_asked < 1]

        if unasked_questions:
            question = random.choice(unasked_questions)
        else:
            # Find the question with the most amount of times asked
            max_asked = max(q_set.questions, key=lambda q: q.num_asked)

            # Repeat the indices of the questions by the amount max_asked - num_asked
            indices = [i for i, q in enumerate(q_set.questions) for _ in range(max_asked.num_asked - q.num_asked + 1)]

            if not indices:
                raise ValueError("No questions available to ask.")
            
            question = q_set.questions[random.choice(indices)]

        # Increment the number of times this question has been asked
        question.num_asked += 1
        return question
    
    def get_random_question_from_all_sets(self) -> Question:
        """Get a random question from all available question sets."""
        all_sets = self.get_all_question_sets()
        print(f"Available question sets: {[q_set.name for q_set in all_sets]}")
        if not all_sets:
            raise ValueError("No question sets available.")
        
        q_set = random.choice(all_sets)
        return self.get_random_question(q_set)