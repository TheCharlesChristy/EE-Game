"""Round orchestration runtime."""

from __future__ import annotations

import datetime
import logging
from typing import Any

from ..core.constants import MSG_STATE_TRANSITION, MSG_STATE_UPDATE, PROTOCOL_VERSION
from ..session.exceptions import InvalidTransitionError
from ..session.models import AuditEvent, SessionStatus
from .exceptions import InvalidRoundTransitionError, NoActiveRoundError, UnknownGameError
from .models import Round, RoundPhase
from .pipeline import build_event_record
from .state_machine import can_transition
from .timer import TimerService

logger = logging.getLogger(__name__)


class RoundService:
    def __init__(
        self,
        *,
        repo: Any,
        manager: Any,
        session_service: Any,
        game_registry: Any,
        scoring_service: Any,
    ) -> None:
        self._repo = repo
        self._manager = manager
        self._session_service = session_service
        self._game_registry = game_registry
        self._scoring_service = scoring_service
        self._timer = TimerService()
        self._current: Round | None = None

    @property
    def current_round(self) -> Round | None:
        return self._current

    async def select_round(self, game_id: str, duration_ms: int | None = None) -> Round:
        session = self._require_active_session()
        game = self._game_registry.get(game_id)
        if game is None:
            raise UnknownGameError(f"Unknown game_id {game_id!r}")

        timer_ms = duration_ms or game.metadata.estimated_seconds * 1000
        round_state = Round.new(session_id=session.id, game_id=game_id, timer_total_ms=timer_ms)
        self._current = round_state
        session.current_round_id = round_state.id
        session.active_game = game_id
        session.updated_at = datetime.datetime.now(datetime.UTC)
        await self._repo.upsert_round(round_state.to_record())
        await self._repo.upsert_session(session)
        await self._repo.insert_audit_event(
            AuditEvent.new(
                session_id=session.id,
                action_type="round_selected",
                payload_summary=f"round_id={round_state.id} game_id={game_id}",
            )
        )
        await self._broadcast("round_selected", self._round_payload(round_state))
        return round_state

    async def transition(self, target: RoundPhase | str) -> Round:
        round_state = await self._require_round()
        target_phase = RoundPhase(target)
        if not can_transition(round_state.phase, target_phase):
            raise InvalidRoundTransitionError(
                f"Cannot transition round from {round_state.phase.value} to {target_phase.value}."
            )

        if round_state.phase == RoundPhase.LIVE and target_phase == RoundPhase.PAUSED:
            self._timer.pause(round_state)
        if target_phase == RoundPhase.LIVE:
            if round_state.started_at is None:
                round_state.started_at = datetime.datetime.now(datetime.UTC)
            self._timer.enter_live(round_state)
        if target_phase == RoundPhase.COMPLETED:
            if round_state.phase == RoundPhase.LIVE:
                self._timer.pause(round_state)
            round_state.ended_at = datetime.datetime.now(datetime.UTC)
            round_state.timer_remaining_ms = self._timer.snapshot_remaining_ms(round_state)

        round_state.phase = target_phase
        round_state.updated_at = datetime.datetime.now(datetime.UTC)
        if target_phase != RoundPhase.COMPLETED:
            await self._repo.upsert_round(round_state.to_record())
        await self._repo.insert_audit_event(
            AuditEvent.new(
                session_id=round_state.session_id,
                action_type="round_transitioned",
                payload_summary=f"round_id={round_state.id} phase={target_phase.value}",
            )
        )

        if target_phase == RoundPhase.COMPLETED:
            return await self.complete_round()

        await self._broadcast("round_transitioned", self._round_payload(round_state))
        return round_state

    async def complete_round(self) -> Round:
        round_state = await self._require_round()
        if round_state.phase not in {RoundPhase.COMPLETED, RoundPhase.LIVE, RoundPhase.PAUSED}:
            raise InvalidRoundTransitionError(
                f"Cannot complete round from phase {round_state.phase.value}."
            )
        if round_state.phase == RoundPhase.LIVE:
            self._timer.pause(round_state)
        round_state.phase = RoundPhase.COMPLETED
        round_state.ended_at = round_state.ended_at or datetime.datetime.now(datetime.UTC)
        round_state.updated_at = datetime.datetime.now(datetime.UTC)
        round_state.timer_remaining_ms = self._timer.snapshot_remaining_ms(round_state)
        await self._repo.upsert_round(round_state.to_record())

        session = self._require_active_session()
        result = await self._scoring_service.score_round(round_state, session.players)
        round_state.result = result
        round_state.phase = RoundPhase.RESULTS
        round_state.updated_at = datetime.datetime.now(datetime.UTC)
        await self._repo.upsert_round(round_state.to_record())
        await self._broadcast("round_completed", self._round_payload(round_state))
        return round_state

    async def enter_intermission(self) -> Round:
        return await self.transition(RoundPhase.INTERMISSION)

    async def handle_test_event(
        self,
        *,
        device_id: str,
        payload: dict[str, Any],
        player: dict[str, Any] | None,
    ) -> dict[str, Any]:
        round_state = await self._require_round()
        if round_state.phase not in {RoundPhase.TEST, RoundPhase.READY}:
            return {
                "accepted": False,
                "code": "WRONG_PHASE",
                "message": f"Test events are not accepted during {round_state.phase.value}.",
            }
        game = self._game_registry.require(round_state.game_id)
        passed, reason = game.validate_test_event(payload, player=player)
        event = build_event_record(
            round_state=round_state,
            device_id=device_id,
            payload=payload,
            phase=RoundPhase.TEST.value,
            player=player,
        )
        await self._repo.insert_round_event(event)
        key = player.get("player_id") if player else device_id
        round_state.test_results[key] = {
            "passed": passed,
            "reason": reason,
            "device_id": device_id,
            "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        }
        round_state.updated_at = datetime.datetime.now(datetime.UTC)
        await self._repo.upsert_round(round_state.to_record())
        await self._broadcast("test_event_recorded", self._round_payload(round_state))
        return {"accepted": passed, "message": reason, "code": "TEST_FAILED" if not passed else "OK"}

    async def handle_device_event(
        self,
        *,
        device_id: str,
        payload: dict[str, Any],
        player: dict[str, Any] | None,
    ) -> dict[str, Any]:
        round_state = await self._require_round()
        if round_state.phase != RoundPhase.LIVE:
            return {
                "accepted": False,
                "code": "WRONG_PHASE",
                "message": f"Live events are not accepted during {round_state.phase.value}.",
            }
        dedupe_key = payload.get("dedupe_key")
        if dedupe_key and await self._repo.has_round_event_dedupe_key(round_state.id, dedupe_key):
            return {"accepted": True, "message": "Duplicate event ignored."}

        event = build_event_record(
            round_state=round_state,
            device_id=device_id,
            payload=payload,
            phase=RoundPhase.LIVE.value,
            player=player,
        )
        game = self._game_registry.require(round_state.game_id)
        round_state.game_state = game.handle_live_event(round_state.game_state, event)
        round_state.timer_remaining_ms = self._timer.snapshot_remaining_ms(round_state)
        round_state.updated_at = datetime.datetime.now(datetime.UTC)
        await self._repo.insert_round_event(event)
        await self._repo.upsert_round(round_state.to_record())
        await self._broadcast("round_event_recorded", self._round_payload(round_state))
        return {"accepted": True, "message": "Event recorded."}

    async def get_current_round(self) -> Round | None:
        if self._current is not None:
            self._current.timer_remaining_ms = self._timer.snapshot_remaining_ms(self._current)
            return self._current
        session = self._session_service.current_session
        if session is None or not session.current_round_id:
            return None
        record = await self._repo.get_round_by_id(session.current_round_id)
        if record is None:
            return None
        self._current = Round.from_record(record)
        return self._current

    async def list_current_events(self) -> list[dict[str, Any]]:
        round_state = await self._require_round()
        return await self._repo.list_round_events(round_state.id)

    def restore_round(self, round_state: Round) -> None:
        self._current = round_state

    async def _require_round(self) -> Round:
        round_state = await self.get_current_round()
        if round_state is None:
            raise NoActiveRoundError("No active round is selected.")
        return round_state

    def _require_active_session(self) -> Any:
        session = self._session_service.current_session
        if session is None:
            raise InvalidTransitionError("No active session exists.")
        if session.status == SessionStatus.FINISHED:
            raise InvalidTransitionError("Finished sessions cannot be modified.")
        return session

    async def _broadcast(self, event: str, data: dict[str, Any]) -> None:
        try:
            await self._manager.broadcast_to_frontends(
                {
                    "version": PROTOCOL_VERSION,
                    "type": MSG_STATE_UPDATE,
                    "payload": {"event": event, "data": data},
                }
            )
            if event in {"round_selected", "round_transitioned", "round_completed"}:
                await self._manager.broadcast_to_devices(
                    {
                        "version": PROTOCOL_VERSION,
                        "type": MSG_STATE_TRANSITION,
                        "payload": {
                            "round_id": data.get("round_id"),
                            "phase": data.get("phase"),
                            "led_state": _led_state_for_phase(str(data.get("phase"))),
                            "remaining_ms": data.get("timer_remaining_ms", 0),
                        },
                    }
                )
        except Exception:
            logger.error("Failed to broadcast round event=%s", event, exc_info=True)

    def _round_payload(self, round_state: Round) -> dict[str, Any]:
        payload = round_state.to_dict()
        game = self._game_registry.get(round_state.game_id)
        if game is not None:
            payload["game"] = game.metadata.to_dict()
        return payload


def _led_state_for_phase(phase: str) -> str:
    if phase == RoundPhase.LIVE.value:
        return "live"
    if phase in {RoundPhase.BUILD.value, RoundPhase.TEST.value, RoundPhase.READY.value}:
        return "connected"
    if phase == RoundPhase.PAUSED.value:
        return "test_fault"
    return "connected"
