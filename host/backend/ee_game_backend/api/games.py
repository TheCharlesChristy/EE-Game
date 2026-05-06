"""Game catalogue API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/games", tags=["games"])


class GameListResponse(BaseModel):
    games: list[dict]
    count: int


@router.get("", response_model=GameListResponse)
async def list_games(
    request: Request,
    category: str | None = None,
    team_capable: bool | None = Query(default=None),
) -> GameListResponse:
    registry = request.app.state.game_registry
    games = [
        game.metadata.to_dict()
        for game in registry.all(category=category, team_capable=team_capable)
    ]
    return GameListResponse(games=games, count=len(games))


@router.get("/{game_id}")
async def get_game(game_id: str, request: Request) -> dict:
    registry = request.app.state.game_registry
    game = registry.get(game_id)
    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown game_id {game_id!r}",
        )
    return game.setup_content(players=[], teams=[])
