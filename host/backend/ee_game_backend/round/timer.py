"""Round timer helper."""

from __future__ import annotations

import time

from .models import Round, RoundPhase


class TimerService:
    """Tracks live countdown time while preserving persisted remaining time."""

    def __init__(self) -> None:
        self._live_started_monotonic: dict[str, float] = {}

    def enter_live(self, round_state: Round) -> None:
        self._live_started_monotonic[round_state.id] = time.monotonic()

    def pause(self, round_state: Round) -> None:
        started = self._live_started_monotonic.pop(round_state.id, None)
        if started is None:
            return
        elapsed_ms = int((time.monotonic() - started) * 1000)
        round_state.timer_remaining_ms = max(0, round_state.timer_remaining_ms - elapsed_ms)

    def snapshot_remaining_ms(self, round_state: Round) -> int:
        if round_state.phase != RoundPhase.LIVE:
            return round_state.timer_remaining_ms
        started = self._live_started_monotonic.get(round_state.id)
        if started is None:
            return round_state.timer_remaining_ms
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return max(0, round_state.timer_remaining_ms - elapsed_ms)
