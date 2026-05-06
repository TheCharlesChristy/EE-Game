"""Game catalogue package."""

from .contract import Game, GameMetadata, GameResult
from .registry import GameRegistry

__all__ = ["Game", "GameMetadata", "GameResult", "GameRegistry"]
