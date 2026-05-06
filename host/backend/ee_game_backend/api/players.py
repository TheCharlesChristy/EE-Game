"""
Player registry REST API for EP-03.
SRS reference: FR-011–FR-018, FR-020, FR-021.
"""

import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from ..registry.exceptions import NoActiveSessionError, PlayerNotFoundError, ValidationError
from ..registry.models import Player

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions/current/players")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class PlayerResponse(BaseModel):
    player_id: str
    device_id: str
    username: str
    colour: str
    connection_state: str
    last_seen_at: str
    registered_at: str
    firmware_version: str
    board_target: str


class PlayerListResponse(BaseModel):
    players: list[PlayerResponse]
    count: int


class UpdatePlayerRequest(BaseModel):
    username: str | None = None
    colour: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _player_to_response(player: Player) -> PlayerResponse:
    return PlayerResponse(
        player_id=player.player_id,
        device_id=player.device_id,
        username=player.username,
        colour=player.colour,
        connection_state=player.connection_state,
        last_seen_at=player.last_seen_at.isoformat(),
        registered_at=player.registered_at.isoformat(),
        firmware_version=player.firmware_version,
        board_target=player.board_target,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=PlayerListResponse)
async def list_players(request: Request) -> PlayerListResponse:
    """
    Return all players registered in the current session.

    Returns an empty list if no session is active — never returns 4xx for
    a missing session.
    SRS: FR-013, FR-016.
    """
    registry = request.app.state.registry
    players = await registry.get_all_players()
    responses = [_player_to_response(p) for p in players]
    return PlayerListResponse(players=responses, count=len(responses))


@router.patch("/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: str,
    body: UpdatePlayerRequest,
    request: Request,
) -> PlayerResponse:
    """
    Update username and/or colour for a registered player.

    At least one of username or colour must be provided in the request body.
    Returns the updated player on success.
    SRS: FR-014, FR-015, FR-017.
    """
    if body.username is None and body.colour is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of 'username' or 'colour' must be provided.",
        )

    registry = request.app.state.registry
    player: Player | None = None

    try:
        if body.username is not None:
            player = await registry.update_player_username(player_id, body.username)
        if body.colour is not None:
            player = await registry.update_player_colour(player_id, body.colour)
    except NoActiveSessionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )

    # player is always set here because we checked that at least one field is present above.
    assert player is not None
    return _player_to_response(player)
