"""Round domain models."""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RoundPhase(StrEnum):
    SELECTED = "selected"
    BUILD = "build"
    TEST = "test"
    READY = "ready"
    LIVE = "live"
    PAUSED = "paused"
    COMPLETED = "completed"
    RESULTS = "results"
    INTERMISSION = "intermission"


@dataclass
class Round:
    id: str
    session_id: str
    game_id: str
    phase: RoundPhase
    created_at: datetime.datetime
    updated_at: datetime.datetime
    timer_total_ms: int
    timer_remaining_ms: int
    started_at: datetime.datetime | None = None
    ended_at: datetime.datetime | None = None
    game_state: dict[str, Any] = field(default_factory=dict)
    test_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    result: dict[str, Any] | None = None

    @staticmethod
    def new(session_id: str, game_id: str, timer_total_ms: int) -> "Round":
        now = datetime.datetime.utcnow()
        return Round(
            id=str(uuid.uuid4()),
            session_id=session_id,
            game_id=game_id,
            phase=RoundPhase.SELECTED,
            created_at=now,
            updated_at=now,
            timer_total_ms=timer_total_ms,
            timer_remaining_ms=timer_total_ms,
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "game_id": self.game_id,
            "phase": self.phase.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "timer_total_ms": self.timer_total_ms,
            "timer_remaining_ms": self.timer_remaining_ms,
            "round_payload": {
                "game_state": self.game_state,
                "test_results": self.test_results,
                "result": self.result,
            },
        }

    @staticmethod
    def from_record(record: dict[str, Any]) -> "Round":
        payload = record.get("round_payload", {})
        return Round(
            id=record["id"],
            session_id=record["session_id"],
            game_id=record["game_id"],
            phase=RoundPhase(record["phase"]),
            created_at=_parse_dt(record["created_at"]),
            updated_at=_parse_dt(record["updated_at"]),
            started_at=_parse_dt(record.get("started_at")),
            ended_at=_parse_dt(record.get("ended_at")),
            timer_total_ms=int(record["timer_total_ms"]),
            timer_remaining_ms=int(record["timer_remaining_ms"]),
            game_state=payload.get("game_state", {}),
            test_results=payload.get("test_results", {}),
            result=payload.get("result"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "round_id": self.id,
            "session_id": self.session_id,
            "game_id": self.game_id,
            "phase": self.phase.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "timer_total_ms": self.timer_total_ms,
            "timer_remaining_ms": self.timer_remaining_ms,
            "game_state": self.game_state,
            "test_results": self.test_results,
            "result": self.result,
        }


def _parse_dt(value: Any) -> datetime.datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value
    return datetime.datetime.fromisoformat(value)
