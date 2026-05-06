"""Explicit round phase transition rules."""

from __future__ import annotations

from .models import RoundPhase

ALLOWED_TRANSITIONS: dict[RoundPhase, set[RoundPhase]] = {
    RoundPhase.SELECTED: {RoundPhase.BUILD},
    RoundPhase.BUILD: {RoundPhase.TEST, RoundPhase.SELECTED},
    RoundPhase.TEST: {RoundPhase.READY, RoundPhase.BUILD},
    RoundPhase.READY: {RoundPhase.LIVE, RoundPhase.TEST},
    RoundPhase.LIVE: {RoundPhase.PAUSED, RoundPhase.COMPLETED},
    RoundPhase.PAUSED: {RoundPhase.LIVE, RoundPhase.COMPLETED},
    RoundPhase.COMPLETED: {RoundPhase.RESULTS},
    RoundPhase.RESULTS: {RoundPhase.INTERMISSION},
    RoundPhase.INTERMISSION: {RoundPhase.SELECTED},
}


def can_transition(source: RoundPhase, target: RoundPhase) -> bool:
    return target in ALLOWED_TRANSITIONS.get(source, set())
