"""Deterministic round-local team allocation."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TeamAllocation:
    team_id: str
    team_name: str
    player_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "player_ids": self.player_ids,
        }


def allocate_teams(
    players: list[dict[str, Any]],
    team_size: int,
    seed: int | str | None = None,
) -> list[TeamAllocation]:
    if team_size < 2:
        raise ValueError("team_size must be at least 2")
    player_ids = [p["player_id"] for p in players if p.get("player_id")]
    rng = random.Random(str(seed) if seed is not None else None)
    rng.shuffle(player_ids)

    team_count = max(1, (len(player_ids) + team_size - 1) // team_size)
    buckets = [[] for _ in range(team_count)]
    for index, player_id in enumerate(player_ids):
        buckets[index % team_count].append(player_id)

    return [
        TeamAllocation(
            team_id=f"team-{idx + 1}",
            team_name=f"Team {idx + 1}",
            player_ids=sorted(bucket),
        )
        for idx, bucket in enumerate(buckets)
        if bucket
    ]


def to_assignment_records(
    *,
    session_id: str,
    round_id: str,
    teams: list[TeamAllocation],
) -> list[dict[str, Any]]:
    import datetime

    now = datetime.datetime.utcnow()
    records: list[dict[str, Any]] = []
    for team in teams:
        for player_id in team.player_ids:
            records.append(
                {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "round_id": round_id,
                    "team_id": team.team_id,
                    "team_name": team.team_name,
                    "player_id": player_id,
                    "created_at": now,
                }
            )
    return records
