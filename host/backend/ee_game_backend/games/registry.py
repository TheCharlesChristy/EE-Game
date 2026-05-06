"""Built-in game registry."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Iterable

from .contract import Game

BUILTIN_GAME_MODULES = [
    "ee_game_backend.games.reaction_race.logic",
    "ee_game_backend.games.quick_quiz_buzzer.logic",
    "ee_game_backend.games.analog_dial_match.logic",
    "ee_game_backend.games.pattern_memory.logic",
    "ee_game_backend.games.wire_the_circuit.logic",
    "ee_game_backend.games.morse_decode.logic",
    "ee_game_backend.games.tug_of_war.logic",
    "ee_game_backend.games.voltage_estimate.logic",
    "ee_game_backend.games.sequence_tap.logic",
    "ee_game_backend.games.color_code_speed_round.logic",
]


@dataclass(frozen=True)
class GameRegistry:
    games: dict[str, Game]

    @classmethod
    def load_builtin(cls, modules: Iterable[str] | None = None) -> "GameRegistry":
        loaded: dict[str, Game] = {}
        for module_name in modules or BUILTIN_GAME_MODULES:
            module = importlib.import_module(module_name)
            game_cls = getattr(module, "GameImpl", None)
            if game_cls is None:
                raise ValueError(f"{module_name} does not expose GameImpl")
            game = game_cls()
            _validate_game(game)
            if game.metadata.id in loaded:
                raise ValueError(f"Duplicate game id: {game.metadata.id}")
            loaded[game.metadata.id] = game
        return cls(games=loaded)

    def all(
        self,
        category: str | None = None,
        team_capable: bool | None = None,
    ) -> list[Game]:
        games = list(self.games.values())
        if category:
            games = [game for game in games if game.metadata.category == category]
        if team_capable is not None:
            games = [game for game in games if game.metadata.team_capable is team_capable]
        return sorted(games, key=lambda game: game.metadata.title)

    def get(self, game_id: str) -> Game | None:
        return self.games.get(game_id)

    def require(self, game_id: str) -> Game:
        game = self.get(game_id)
        if game is None:
            raise KeyError(f"Unknown game_id {game_id!r}")
        return game


def _validate_game(game: Game) -> None:
    metadata = game.metadata
    required = [
        metadata.id,
        metadata.title,
        metadata.category,
        metadata.summary,
        metadata.input_modes,
        metadata.materials,
        metadata.build_instructions,
    ]
    if any(not value for value in required):
        raise ValueError(f"Game {metadata.id!r} has incomplete metadata")
    if metadata.min_players < 1 or metadata.max_players < metadata.min_players:
        raise ValueError(f"Game {metadata.id!r} has invalid player limits")
    if metadata.team_capable and not metadata.team_size:
        raise ValueError(f"Game {metadata.id!r} must declare team_size")
