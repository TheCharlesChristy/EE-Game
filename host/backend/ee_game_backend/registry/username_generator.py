"""
Username generator for EP-03 (Player and Device Registry).
SRS reference: FR-012, Section 8.3.
"""

import logging
import random

logger = logging.getLogger(__name__)

ADJECTIVES: list[str] = [
    "Brave",
    "Clever",
    "Swift",
    "Bold",
    "Calm",
    "Keen",
    "Cool",
    "Dark",
    "Fast",
    "Loud",
]

NOUNS: list[str] = [
    "Fox",
    "Wolf",
    "Hawk",
    "Bear",
    "Lion",
    "Shark",
    "Owl",
    "Crab",
    "Frog",
    "Wasp",
]


class UsernameGenerator:
    """
    Session-scoped username generator.

    Builds a shuffled pool of all 100 adjective+noun combinations (PascalCase).
    Each call to generate() returns the next name from the pool that is not in
    the caller-supplied exclude list.  If the pool is exhausted a numeric suffix
    is appended to cycle through names again.
    """

    def __init__(self, seed: int | None = None) -> None:
        """
        Initialise the generator with a shuffled pool.

        Args:
            seed: Optional RNG seed for reproducible output in tests.
                  Pass None (default) for unpredictable random order.
        """
        rng = random.Random(seed)
        self._pool: list[str] = [
            f"{adj}{noun}" for adj in ADJECTIVES for noun in NOUNS
        ]
        rng.shuffle(self._pool)
        self._index: int = 0
        self._suffix_counter: int = 2

    def generate(self, exclude: list[str]) -> str:
        """
        Return the next unused adjective+noun combination not present in exclude.

        Iterates the shuffled pool sequentially.  When the pool is exhausted
        (all 100 combinations have been used — this should never happen with ≤20
        devices) the generator appends an incrementing numeric suffix (e.g.
        "BraveFox2", "BraveFox3") to ensure uniqueness.

        Args:
            exclude: List of usernames already assigned in the current session.

        Returns:
            A PascalCase username string.
        """
        exclude_set = set(exclude)

        # First pass: iterate remaining pool entries.
        while self._index < len(self._pool):
            name = self._pool[self._index]
            self._index += 1
            if name not in exclude_set:
                return name

        # Pool exhausted — append numeric suffix until we find an unused name.
        logger.warning(
            "UsernameGenerator pool exhausted after %d names; appending numeric suffix",
            len(self._pool),
        )
        for base in self._pool:
            candidate = f"{base}{self._suffix_counter}"
            self._suffix_counter += 1
            if candidate not in exclude_set:
                return candidate

        # Extremely unlikely: all suffixed names are also taken.
        # Fall back to a guaranteed-unique UUID-derived name.
        import uuid

        fallback = f"Player{uuid.uuid4().hex[:6].upper()}"
        logger.error(
            "UsernameGenerator could not find any unused name; using fallback=%s", fallback
        )
        return fallback
