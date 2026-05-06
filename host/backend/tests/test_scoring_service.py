from unittest.mock import AsyncMock

import pytest

from ee_game_backend.core.connection_manager import ConnectionManager
from ee_game_backend.games.registry import GameRegistry
from ee_game_backend.round.models import Round, RoundPhase
from ee_game_backend.scoring.exceptions import ManualAdjustmentRejected
from ee_game_backend.scoring.service import ScoringService
from ee_game_backend.session.database import open_database
from ee_game_backend.session.repository import SessionRepository
from ee_game_backend.session.service import SessionService


async def test_manual_adjustment_requires_intermission():
    db = await open_database(":memory:")
    repo = SessionRepository(db)
    manager = ConnectionManager()
    manager.broadcast_to_frontends = AsyncMock()
    session_service = SessionService(repo, manager)
    registry = GameRegistry.load_builtin()
    scoring = ScoringService(repo, manager, session_service, registry)
    session = await session_service.create_session()
    round_state = Round.new(session.id, "reaction_race", 1000)
    round_state.phase = RoundPhase.RESULTS
    session.current_round_id = round_state.id
    await repo.upsert_round(round_state.to_record())
    await repo.upsert_session(session)

    with pytest.raises(ManualAdjustmentRejected):
        await scoring.apply_manual_adjustment(player_id="p1", score_delta=1, reason="late correction")

    await db.close()
