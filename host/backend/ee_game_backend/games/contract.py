"""Game contract used by the backend runtime and built-in catalogue."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class GameMetadata:
    id: str
    title: str
    category: str
    summary: str
    min_players: int
    max_players: int
    estimated_seconds: int
    input_modes: list[str]
    materials: list[str]
    build_instructions: list[str]
    team_capable: bool = False
    team_size: int | None = None
    scoring_mode: str = "points"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GameResult:
    round_id: str
    game_id: str
    player_scores: dict[str, int] = field(default_factory=dict)
    team_scores: dict[str, int] = field(default_factory=dict)
    highlights: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Game(ABC):
    """Abstract contract all games must implement."""

    metadata: GameMetadata

    @abstractmethod
    def setup_content(
        self,
        players: list[dict[str, Any]],
        teams: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Return build/test/live copy and setup data for the selected round."""

    @abstractmethod
    def validate_test_event(
        self,
        event_payload: dict[str, Any],
        player: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Validate a test-phase event, returning (passed, reason)."""

    @abstractmethod
    def handle_live_event(
        self,
        state: dict[str, Any],
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """Reduce one live event into the round-local game state."""

    @abstractmethod
    def score_round(
        self,
        round_id: str,
        events: list[dict[str, Any]],
        players: list[dict[str, Any]],
        teams: list[dict[str, Any]] | None = None,
    ) -> GameResult:
        """Compute deterministic score output from the persisted round event log."""

    @abstractmethod
    def format_result(self, result: GameResult) -> dict[str, Any]:
        """Return a frontend-friendly result payload."""
