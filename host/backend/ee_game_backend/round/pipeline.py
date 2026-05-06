"""Round event pipeline."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from .models import Round


def build_event_record(
    *,
    round_state: Round,
    device_id: str,
    payload: dict[str, Any],
    phase: str,
    player: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "session_id": round_state.session_id,
        "round_id": round_state.id,
        "player_id": player.get("player_id") if player else None,
        "device_id": device_id,
        "event_type": str(payload.get("event_type")),
        "phase": phase,
        "dedupe_key": payload.get("dedupe_key"),
        "event_payload": payload,
        "received_at": datetime.datetime.utcnow(),
    }
