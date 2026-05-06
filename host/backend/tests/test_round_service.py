from unittest.mock import AsyncMock

from ee_game_backend.core.connection_manager import ConnectionManager
from ee_game_backend.games.registry import GameRegistry
from ee_game_backend.round.models import RoundPhase
from ee_game_backend.round.service import RoundService
from ee_game_backend.scoring.service import ScoringService
from ee_game_backend.session.database import open_database
from ee_game_backend.session.repository import SessionRepository
from ee_game_backend.session.service import SessionService

async def test_round_transitions_and_scores_event():
    db = await open_database(":memory:")
    repo = SessionRepository(db)
    manager = ConnectionManager()
    manager.broadcast_to_frontends = AsyncMock()
    manager.broadcast_to_devices = AsyncMock()
    session_service = SessionService(repo=repo, manager=manager)
    registry = GameRegistry.load_builtin()
    scoring = ScoringService(repo, manager, session_service, registry)
    rounds = RoundService(
        repo=repo,
        manager=manager,
        session_service=session_service,
        game_registry=registry,
        scoring_service=scoring,
    )
    try:
        session = await session_service.create_session()
        session.players = [
            {
                "player_id": "p1",
                "device_id": "d1",
                "username": "Alex",
                "colour": "#2E86AB",
            }
        ]
        await repo.upsert_session(session)

        round_state = await rounds.select_round("reaction_race", duration_ms=10_000)
        assert round_state.phase == RoundPhase.SELECTED
        await rounds.transition(RoundPhase.BUILD)
        await rounds.transition(RoundPhase.TEST)
        await rounds.handle_test_event(
            device_id="d1",
            payload={"event_type": "button"},
            player=session.players[0],
        )
        await rounds.transition(RoundPhase.READY)
        await rounds.transition(RoundPhase.LIVE)
        await rounds.handle_device_event(
            device_id="d1",
            payload={
                "event_type": "button",
                "dedupe_key": "evt-1",
                "correct": True,
                "elapsed_ms": 200,
            },
            player=session.players[0],
        )
        completed = await rounds.complete_round()
        assert completed.phase == RoundPhase.RESULTS
        assert session_service.current_session.standings[0]["player_id"] == "p1"
    finally:
        await db.close()
