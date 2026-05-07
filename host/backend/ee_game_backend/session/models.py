"""
Session domain models for EP-02.
SRS reference: FR-001–FR-010, Section 9.2, Section 9.3.
"""

import datetime
import hashlib
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SessionStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    FINISHED = "finished"


@dataclass
class Session:
    """
    In-memory authoritative session state.

    Fields mirror SRS Section 9.3 minimum fields for the Session entity,
    plus a payload blob for round/player state (populated by later epics).
    """

    id: str
    status: SessionStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    # Populated by EP-05/EP-06 (round orchestration) — None until then.
    current_round_id: str | None = None
    # Populated by EP-03 (player registry) — empty list until then.
    players: list[dict] = field(default_factory=list)
    # Populated by EP-07 (scoring) — empty list until then.
    standings: list[dict] = field(default_factory=list)
    # Active game name — populated by EP-05.
    active_game: str | None = None

    @staticmethod
    def new() -> "Session":
        now = datetime.datetime.now(datetime.UTC)
        return Session(
            id=str(uuid.uuid4()),
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    def to_payload_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict for persistence."""
        return {
            "id": self.id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "current_round_id": self.current_round_id,
            "players": self.players,
            "standings": self.standings,
            "active_game": self.active_game,
        }

    @staticmethod
    def from_payload_dict(data: dict[str, Any]) -> "Session":
        """Deserialise from a persisted payload dict."""
        return Session(
            id=data["id"],
            status=SessionStatus(data["status"]),
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.datetime.fromisoformat(data["updated_at"]),
            current_round_id=data.get("current_round_id"),
            players=data.get("players", []),
            standings=data.get("standings", []),
            active_game=data.get("active_game"),
        )


@dataclass
class SessionArchive:
    """
    Immutable finished archive record.
    SRS reference: Section 9.2 SessionArchive, Section 9.4.
    Usernames are anonymised; player references use positional labels.
    """

    id: str
    session_id: str
    finished_at: datetime.datetime
    anonymised_payload: dict[str, Any]
    retention_state: str = "retained"

    @staticmethod
    def from_session(session: "Session") -> "SessionArchive":
        """
        Create an anonymised archive from a finished session.
        Removes direct usernames; preserves standings/round order/scores.
        SRS reference: Section 9.4 Archive Anonymisation Rules.
        """
        anon_players = [
            {
                "archive_label": f"Player_{i + 1}",
                "colour": p.get("colour"),
                "cumulative_score": p.get("cumulative_score", 0),
            }
            for i, p in enumerate(session.players)
        ]
        return SessionArchive(
            id=str(uuid.uuid4()),
            session_id=session.id,
            finished_at=datetime.datetime.now(datetime.UTC),
            anonymised_payload={
                "session_id": session.id,
                "created_at": session.created_at.isoformat(),
                "finished_at": datetime.datetime.now(datetime.UTC).isoformat(),
                "players": anon_players,
                "standings": session.standings,
                "active_game": session.active_game,
            },
        )


@dataclass
class AuditEvent:
    """
    Audit record for lifecycle and administrative actions.
    SRS reference: Section 9.2 AuditEvent, Section 14.3.
    """

    id: str
    session_id: str | None
    action_type: str
    actor_type: str
    payload_summary: str
    created_at: datetime.datetime

    @staticmethod
    def new(
        session_id: str | None,
        action_type: str,
        actor_type: str = "host",
        payload_summary: str = "",
    ) -> "AuditEvent":
        return AuditEvent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            action_type=action_type,
            actor_type=actor_type,
            payload_summary=payload_summary,
            created_at=datetime.datetime.now(datetime.UTC),
        )


def compute_checksum(payload_json: str) -> str:
    """SHA-256 checksum of a JSON payload string for corruption detection."""
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
