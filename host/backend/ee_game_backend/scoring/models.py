"""Scoring models."""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScoreDelta:
    session_id: str
    round_id: str
    score_delta: int
    reason: str
    source: str
    player_id: str | None = None
    team_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "round_id": self.round_id,
            "player_id": self.player_id,
            "team_id": self.team_id,
            "score_delta": self.score_delta,
            "reason": self.reason,
            "source": self.source,
            "payload": self.payload,
            "created_at": self.created_at,
        }
