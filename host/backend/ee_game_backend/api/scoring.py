"""Scoring and manual adjustment API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..scoring.exceptions import ManualAdjustmentRejected

router = APIRouter(prefix="/api/scoring", tags=["scoring"])


class ManualAdjustmentRequest(BaseModel):
    player_id: str
    score_delta: int = Field(ge=-1000, le=1000)
    reason: str = Field(min_length=1, max_length=240)


@router.get("/standings")
async def get_standings(request: Request) -> dict:
    session = request.app.state.session_service.current_session
    if session is None:
        return {"standings": []}
    return {"standings": session.standings}


@router.post("/adjust")
async def apply_manual_adjustment(body: ManualAdjustmentRequest, request: Request) -> dict:
    try:
        return await request.app.state.scoring_service.apply_manual_adjustment(
            player_id=body.player_id,
            score_delta=body.score_delta,
            reason=body.reason,
        )
    except ManualAdjustmentRejected as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
