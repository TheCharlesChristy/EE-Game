"""Scoring service and deterministic standings recomputation."""

from __future__ import annotations

import logging
from typing import Any

from ..core.constants import MSG_STATE_UPDATE, PROTOCOL_VERSION
from ..round.models import Round, RoundPhase
from ..session.models import AuditEvent
from .exceptions import ManualAdjustmentRejected
from .models import ScoreDelta

logger = logging.getLogger(__name__)


class ScoringService:
    def __init__(
        self,
        repo: Any,
        manager: Any,
        session_service: Any,
        game_registry: Any,
    ) -> None:
        self._repo = repo
        self._manager = manager
        self._session_service = session_service
        self._game_registry = game_registry

    async def score_round(self, round_state: Round, players: list[dict[str, Any]]) -> dict[str, Any]:
        game = self._game_registry.require(round_state.game_id)
        events = await self._repo.list_round_events(round_state.id)
        assignments = await self._repo.list_team_assignments(round_state.id)
        teams = _assignments_to_teams(assignments)
        result = game.score_round(
            round_id=round_state.id,
            events=events,
            players=players,
            teams=teams,
        )
        score_events = [
            ScoreDelta(
                session_id=round_state.session_id,
                round_id=round_state.id,
                player_id=player_id,
                score_delta=score,
                reason=f"{round_state.game_id} round score",
                source="game",
                payload={"game_id": round_state.game_id},
            ).to_record()
            for player_id, score in result.player_scores.items()
            if score != 0
        ]
        score_events.extend(
            ScoreDelta(
                session_id=round_state.session_id,
                round_id=round_state.id,
                team_id=team_id,
                score_delta=score,
                reason=f"{round_state.game_id} team round score",
                source="game_team",
                payload={"game_id": round_state.game_id},
            ).to_record()
            for team_id, score in result.team_scores.items()
            if score != 0
        )
        await self._repo.insert_score_events(score_events)
        await self.recompute_standings(round_state.session_id)
        await self._repo.insert_audit_event(
            AuditEvent.new(
                session_id=round_state.session_id,
                action_type="round_scored",
                payload_summary=f"round_id={round_state.id} game_id={round_state.game_id}",
            )
        )
        return game.format_result(result)

    async def apply_manual_adjustment(
        self,
        *,
        player_id: str,
        score_delta: int,
        reason: str,
    ) -> dict[str, Any]:
        session = self._session_service.current_session
        if session is None or not session.current_round_id:
            raise ManualAdjustmentRejected("Manual adjustments require an active intermission.")
        record = await self._repo.get_round_by_id(session.current_round_id)
        if record is None or RoundPhase(record["phase"]) != RoundPhase.INTERMISSION:
            raise ManualAdjustmentRejected("Manual adjustments are only allowed during intermission.")
        if not reason.strip():
            raise ManualAdjustmentRejected("Manual adjustments require a reason.")

        event = ScoreDelta(
            session_id=session.id,
            round_id=session.current_round_id,
            player_id=player_id,
            score_delta=score_delta,
            reason=reason.strip(),
            source="manual",
        )
        await self._repo.insert_score_events([event.to_record()])
        standings = await self.recompute_standings(session.id)
        await self._repo.insert_audit_event(
            AuditEvent.new(
                session_id=session.id,
                action_type="score_adjusted",
                payload_summary=f"player_id={player_id} delta={score_delta} reason={reason.strip()}",
            )
        )
        await self._broadcast("score_adjusted", {"standings": standings})
        return {"standings": standings, "score_event": event.to_record()}

    async def recompute_standings(self, session_id: str) -> list[dict[str, Any]]:
        session = self._session_service.current_session
        if session is None or session.id != session_id:
            return []
        score_events = await self._repo.list_score_events(session_id)
        totals: dict[str, int] = {}
        for event in score_events:
            player_id = event.get("player_id")
            if not player_id:
                continue
            totals[player_id] = totals.get(player_id, 0) + int(event["score_delta"])

        player_lookup = {p.get("player_id"): p for p in session.players}
        standings = [
            {
                "player_id": player_id,
                "username": player_lookup.get(player_id, {}).get("username", "Player"),
                "colour": player_lookup.get(player_id, {}).get("colour", "#808080"),
                "score": score,
            }
            for player_id, score in totals.items()
        ]
        standings.sort(key=lambda item: (-item["score"], item["username"]))
        session.standings = standings
        await self._repo.upsert_session(session)
        return standings

    async def _broadcast(self, event: str, data: dict[str, Any]) -> None:
        try:
            await self._manager.broadcast_to_frontends(
                {
                    "version": PROTOCOL_VERSION,
                    "type": MSG_STATE_UPDATE,
                    "payload": {"event": event, "data": data},
                }
            )
        except Exception:
            logger.error("Failed to broadcast scoring event=%s", event, exc_info=True)


def _assignments_to_teams(assignments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    teams: dict[str, dict[str, Any]] = {}
    for assignment in assignments:
        team_id = assignment["team_id"]
        team = teams.setdefault(
            team_id,
            {
                "team_id": team_id,
                "team_name": assignment["team_name"],
                "player_ids": [],
            },
        )
        team["player_ids"].append(assignment["player_id"])
    return list(teams.values())
