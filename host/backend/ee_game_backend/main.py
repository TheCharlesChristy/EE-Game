import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .core.logging_config import configure_logging
from .core.connection_manager import ConnectionManager
from .core.message_router import MessageRouter
from .core.heartbeat import heartbeat_monitor
from .api.diagnostics import router as diagnostics_router
from .api.games import router as games_router
from .api.health import router as health_router
from .api.players import router as players_router
from .api.rounds import router as rounds_router
from .api.scoring import router as scoring_router
from .api.session import router as session_router
from .api.teams import router as teams_router
from .api.ws.devices import router as devices_router
from .api.ws.frontend import router as frontend_router
from .games.registry import GameRegistry
from .registry.service import PlayerRegistryService
from .round.models import Round
from .round.service import RoundService
from .scoring.service import ScoringService
from .session.database import open_database
from .session.recovery import run_recovery
from .session.repository import SessionRepository
from .session.service import SessionService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info(
        "EE-Game backend starting (port=%d, log_level=%s)",
        settings.backend_port,
        settings.log_level,
    )

    # Persistence layer
    db = await open_database(settings.db_path)
    repo = SessionRepository(db)

    # Shared singletons
    app.state.connection_manager = ConnectionManager()
    app.state.message_router = MessageRouter()
    app.state.repo = repo
    app.state.game_registry = GameRegistry.load_builtin()
    app.state.session_service = SessionService(repo=repo, manager=app.state.connection_manager)
    app.state.scoring_service = ScoringService(
        repo=repo,
        manager=app.state.connection_manager,
        session_service=app.state.session_service,
        game_registry=app.state.game_registry,
    )
    app.state.round_service = RoundService(
        repo=repo,
        manager=app.state.connection_manager,
        session_service=app.state.session_service,
        game_registry=app.state.game_registry,
        scoring_service=app.state.scoring_service,
    )
    app.state.registry = PlayerRegistryService(
        session_service=app.state.session_service,
        repo=repo,
        manager=app.state.connection_manager,
    )
    app.state.db = db

    # Startup recovery — restore latest consistent session if one exists (FR-009, Section 13.3)
    recovery_result = await run_recovery(repo=repo, service=app.state.session_service)
    logger.info("Startup recovery: %s", recovery_result.message)
    if (
        app.state.session_service.current_session is not None
        and app.state.session_service.current_session.current_round_id
    ):
        round_record = await repo.get_round_by_id(
            app.state.session_service.current_session.current_round_id
        )
        if round_record is not None:
            app.state.round_service.restore_round(Round.from_record(round_record))

    # Background tasks
    heartbeat_task = None
    if "PYTEST_CURRENT_TEST" not in os.environ:
        heartbeat_task = asyncio.create_task(
            heartbeat_monitor(
                app.state.connection_manager,
                timeout_seconds=settings.heartbeat_timeout_seconds,
                registry=app.state.registry,
            )
        )

    yield

    if heartbeat_task is not None:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

    await app.state.db.close()
    logger.info("EE-Game backend shutting down")


def create_app() -> FastAPI:
    app = FastAPI(title="EE-Game Backend", version="0.1.0", lifespan=lifespan)
    app.include_router(health_router, tags=["infrastructure"])
    app.include_router(session_router, tags=["sessions"])
    app.include_router(players_router, tags=["players"])
    app.include_router(games_router, tags=["games"])
    app.include_router(rounds_router, tags=["rounds"])
    app.include_router(scoring_router, tags=["scoring"])
    app.include_router(teams_router, tags=["teams"])
    app.include_router(diagnostics_router, tags=["diagnostics"])
    app.include_router(devices_router, tags=["websocket"])
    app.include_router(frontend_router, tags=["websocket"])

    # Serve built React frontend as static files if the dist directory exists.
    # This mount is inactive during development (use `npm run dev` separately).
    settings = get_settings()
    static_path = Path(__file__).parent / settings.static_files_dir
    if static_path.exists() and static_path.is_dir():
        app.mount("/", StaticFiles(directory=str(static_path), html=True), name="frontend")
        logger.info("Serving frontend from %s", static_path)

    return app


app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("main:app", host=settings.backend_host, port=settings.backend_port, reload=False)
