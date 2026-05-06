"""Reusable implementation for the first-party event-scored games."""

from __future__ import annotations

from collections import defaultdict
import datetime
from typing import Any

from ..contract import Game, GameMetadata, GameResult


class SimpleEventGame(Game):
    """
    Data-driven game implementation.

    Built-ins can override scoring fields, but they all share the same event
    pipeline contract: test events prove wiring/input readiness, live events add
    immutable entries to the event log, and scores are derived from that log.
    """

    metadata: GameMetadata
    valid_event_types: set[str] = {"input", "answer", "tap", "signal"}
    scoring_events: set[str] = {"input", "answer", "tap", "signal"}
    base_points: int = 10
    correct_bonus: int = 15
    speed_bonus_under_ms: int = 1500
    speed_bonus_points: int = 5

    def setup_content(
        self,
        players: list[dict[str, Any]],
        teams: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "players": players,
            "teams": teams or [],
            "build": {
                "materials": self.metadata.materials,
                "instructions": self.metadata.build_instructions,
            },
            "test": {
                "required_event_types": sorted(self.valid_event_types),
                "message": "Each device must emit one valid test event before live play.",
            },
        }

    def validate_test_event(
        self,
        event_payload: dict[str, Any],
        player: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        event_type = str(event_payload.get("event_type", event_payload.get("kind", "")))
        if event_type not in self.valid_event_types:
            return False, f"Unsupported event_type {event_type!r} for {self.metadata.id}."
        if event_payload.get("fault") is True:
            return False, "Device reported a circuit fault."
        return True, "Input received."

    def handle_live_event(
        self,
        state: dict[str, Any],
        event: dict[str, Any],
    ) -> dict[str, Any]:
        events = list(state.get("events", []))
        safe_event = _json_safe(event)
        events.append(safe_event)
        state = dict(state)
        state["events"] = events
        state["event_count"] = len(events)
        state["last_event"] = safe_event
        return state

    def score_round(
        self,
        round_id: str,
        events: list[dict[str, Any]],
        players: list[dict[str, Any]],
        teams: list[dict[str, Any]] | None = None,
    ) -> GameResult:
        player_scores: dict[str, int] = defaultdict(int)
        player_names = {p.get("player_id"): p.get("username", "Player") for p in players}
        assignments = _team_lookup(teams or [])
        team_scores: dict[str, int] = defaultdict(int)

        for event in events:
            event_type = event.get("event_type")
            if event_type not in self.scoring_events:
                continue
            player_id = event.get("player_id")
            if not player_id:
                continue
            payload = event.get("event_payload", {})
            if payload.get("correct") is False:
                player_scores[player_id] += int(payload.get("score_delta", 0))
                continue

            points = int(payload.get("score_delta", self.base_points))
            if payload.get("correct") is True:
                points += self.correct_bonus
            elapsed_ms = payload.get("elapsed_ms") or payload.get("reaction_ms")
            if isinstance(elapsed_ms, int) and elapsed_ms <= self.speed_bonus_under_ms:
                points += self.speed_bonus_points
            player_scores[player_id] += points

            team_id = assignments.get(player_id)
            if team_id:
                team_scores[team_id] += points

        ranked = sorted(player_scores.items(), key=lambda item: item[1], reverse=True)
        highlights = [
            f"{player_names.get(player_id, 'Player')} scored {score}"
            for player_id, score in ranked[:3]
        ]
        return GameResult(
            round_id=round_id,
            game_id=self.metadata.id,
            player_scores=dict(player_scores),
            team_scores=dict(team_scores),
            highlights=highlights,
            details={"event_count": len(events), "scoring_mode": self.metadata.scoring_mode},
        )

    def format_result(self, result: GameResult) -> dict[str, Any]:
        return result.to_dict()


def _team_lookup(teams: list[dict[str, Any]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for team in teams:
        team_id = team.get("team_id")
        for player_id in team.get("player_ids", []):
            if team_id:
                lookup[player_id] = team_id
    return lookup


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value
