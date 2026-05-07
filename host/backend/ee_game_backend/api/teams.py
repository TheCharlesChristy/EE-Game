"""Team allocation API."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from ..core.constants import MSG_STATE_UPDATE, PROTOCOL_VERSION
from ..scoring.team_allocator import allocate_teams, to_assignment_records
from ..session.models import AuditEvent

router = APIRouter(prefix="/api/teams", tags=["teams"])


class TeamPreviewRequest(BaseModel):
    game_id: str | None = None
    seed: int | str | None = None


@router.post("/preview")
async def preview_teams(body: TeamPreviewRequest, request: Request) -> dict:
    session = request.app.state.session_service.current_session
    if session is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active session.")
    game_id = body.game_id or session.active_game
    if not game_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No game selected.")
    game = request.app.state.game_registry.get(game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown game.")
    if not game.metadata.team_capable or not game.metadata.team_size:
        return {"teams": [], "team_capable": False}
    teams = allocate_teams(session.players, game.metadata.team_size, body.seed)
    return {"teams": [team.to_dict() for team in teams], "team_capable": True}


@router.post("/confirm")
async def confirm_teams(body: TeamPreviewRequest, request: Request) -> dict:
    session = request.app.state.session_service.current_session
    round_state = await request.app.state.round_service.get_current_round()
    if session is None or round_state is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active round.")
    game = request.app.state.game_registry.require(round_state.game_id)
    if not game.metadata.team_capable or not game.metadata.team_size:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game is not team-capable.")
    teams = allocate_teams(session.players, game.metadata.team_size, body.seed)
    records = to_assignment_records(
        session_id=session.id,
        round_id=round_state.id,
        teams=teams,
    )
    await request.app.state.repo.replace_team_assignments(round_state.id, records)
    await request.app.state.repo.insert_audit_event(
        AuditEvent.new(
            session_id=session.id,
            action_type="teams_allocated",
            payload_summary=(
                f"round_id={round_state.id} teams={len(teams)} "
                f"at={datetime.datetime.now(datetime.UTC).isoformat()}"
            ),
        )
    )
    await request.app.state.connection_manager.broadcast_to_frontends(
        {
            "version": PROTOCOL_VERSION,
            "type": MSG_STATE_UPDATE,
            "payload": {
                "event": "teams_allocated",
                "data": {"round_id": round_state.id, "teams": [team.to_dict() for team in teams]},
            },
        }
    )
    return {"teams": [team.to_dict() for team in teams], "team_capable": True}
