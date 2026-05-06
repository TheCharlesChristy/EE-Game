"""Round orchestration API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..round.exceptions import InvalidRoundTransitionError, NoActiveRoundError, UnknownGameError
from ..round.models import RoundPhase
from ..session.exceptions import InvalidTransitionError

router = APIRouter(prefix="/api/rounds", tags=["rounds"])


class SelectRoundRequest(BaseModel):
    game_id: str
    duration_ms: int | None = Field(default=None, ge=1000)


class TransitionRequest(BaseModel):
    phase: RoundPhase


@router.post("/select", status_code=status.HTTP_201_CREATED)
async def select_round(body: SelectRoundRequest, request: Request) -> dict:
    try:
        round_state = await request.app.state.round_service.select_round(
            game_id=body.game_id,
            duration_ms=body.duration_ms,
        )
    except UnknownGameError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return round_state.to_dict()


@router.get("/current")
async def get_current_round(request: Request) -> dict:
    round_state = await request.app.state.round_service.get_current_round()
    if round_state is None:
        return {"round": None}
    return {"round": round_state.to_dict()}


@router.post("/current/transition")
async def transition_round(body: TransitionRequest, request: Request) -> dict:
    try:
        round_state = await request.app.state.round_service.transition(body.phase)
    except NoActiveRoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidRoundTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return round_state.to_dict()


@router.post("/current/complete")
async def complete_round(request: Request) -> dict:
    try:
        round_state = await request.app.state.round_service.complete_round()
    except NoActiveRoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidRoundTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return round_state.to_dict()


@router.post("/current/intermission")
async def enter_intermission(request: Request) -> dict:
    try:
        round_state = await request.app.state.round_service.enter_intermission()
    except NoActiveRoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidRoundTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return round_state.to_dict()


@router.get("/current/events")
async def list_current_round_events(request: Request) -> dict:
    try:
        events = await request.app.state.round_service.list_current_events()
    except NoActiveRoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return {"events": events, "count": len(events)}
