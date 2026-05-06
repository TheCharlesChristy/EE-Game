"""
Unit and integration tests for SessionService (EP-02).
SRS reference: FR-001–FR-010, Section 14.3.

Uses a real in-memory aiosqlite database and a real SessionRepository.
ConnectionManager is mocked with AsyncMock to avoid needing real WebSocket connections.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from ee_game_backend.session.database import open_database
from ee_game_backend.session.exceptions import (
    ActiveSessionExistsError,
    ArchiveError,
    InvalidTransitionError,
    SessionNotFoundError,
)
from ee_game_backend.session.models import Session, SessionStatus
from ee_game_backend.session.repository import SessionRepository
from ee_game_backend.session.service import SessionService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db():
    """Open a fresh in-memory SQLite database for each test."""
    conn = await open_database(":memory:")
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def repo(db):
    """Real SessionRepository backed by the in-memory database."""
    return SessionRepository(db)


@pytest.fixture
def mock_manager():
    """Mock ConnectionManager — broadcast_to_frontends is an AsyncMock."""
    manager = MagicMock()
    manager.broadcast_to_frontends = AsyncMock()
    return manager


@pytest_asyncio.fixture
async def service(repo, mock_manager):
    """Fresh SessionService with a real repo and mocked manager."""
    return SessionService(repo=repo, manager=mock_manager)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


async def _count_audit_events(repo: SessionRepository, action_type: str) -> int:
    async with repo._db.execute(
        "SELECT COUNT(*) AS cnt FROM audit_events WHERE action_type = ?",
        (action_type,),
    ) as cursor:
        row = await cursor.fetchone()
    return row["cnt"] if row else 0


# ---------------------------------------------------------------------------
# create_session tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_session_no_existing_creates_active(service):
    session = await service.create_session()
    assert session.status == SessionStatus.ACTIVE
    assert session.id is not None


@pytest.mark.asyncio
async def test_create_session_persists_to_repo(service, repo):
    session = await service.create_session()
    persisted = await repo.get_session_by_id(session.id)
    assert persisted is not None
    assert persisted.id == session.id
    assert persisted.status == SessionStatus.ACTIVE


@pytest.mark.asyncio
async def test_create_session_emits_audit_event(service, repo):
    await service.create_session()
    count = await _count_audit_events(repo, "session_created")
    assert count == 1


@pytest.mark.asyncio
async def test_create_session_broadcasts_to_frontends(service, mock_manager):
    await service.create_session()
    mock_manager.broadcast_to_frontends.assert_awaited_once()
    call_args = mock_manager.broadcast_to_frontends.call_args[0][0]
    assert call_args["payload"]["event"] == "session_created"


@pytest.mark.asyncio
async def test_create_session_raises_when_active_session_exists(service):
    await service.create_session()
    with pytest.raises(ActiveSessionExistsError):
        await service.create_session()


@pytest.mark.asyncio
async def test_create_session_blocked_logs_and_emits_audit(service, repo):
    await service.create_session()
    with pytest.raises(ActiveSessionExistsError):
        await service.create_session()
    count = await _count_audit_events(repo, "session_create_blocked_concurrent")
    assert count == 1


# ---------------------------------------------------------------------------
# save_session tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_session_active_does_not_change_status(service):
    await service.create_session()
    saved = await service.save_session()
    assert saved.status == SessionStatus.ACTIVE


@pytest.mark.asyncio
async def test_save_session_paused_does_not_change_status(service):
    await service.create_session()
    await service.pause_session()
    saved = await service.save_session()
    assert saved.status == SessionStatus.PAUSED


@pytest.mark.asyncio
async def test_save_session_updates_updated_at(service):
    session = await service.create_session()
    original_ts = session.updated_at
    saved = await service.save_session()
    assert saved.updated_at >= original_ts


@pytest.mark.asyncio
async def test_save_session_emits_audit_event(service, repo):
    await service.create_session()
    await service.save_session()
    count = await _count_audit_events(repo, "session_saved")
    assert count == 1


@pytest.mark.asyncio
async def test_save_session_raises_when_no_session(service):
    with pytest.raises(InvalidTransitionError):
        await service.save_session()


@pytest.mark.asyncio
async def test_save_session_raises_when_finished(service):
    await service.create_session()
    await service.finish_session()
    # In-memory session is now None; inject a finished session to test the guard.
    finished_session = Session.new()
    finished_session.status = SessionStatus.FINISHED
    service._current = finished_session
    with pytest.raises(InvalidTransitionError):
        await service.save_session()


# ---------------------------------------------------------------------------
# pause_session tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pause_session_transitions_active_to_paused(service):
    await service.create_session()
    paused = await service.pause_session()
    assert paused.status == SessionStatus.PAUSED


@pytest.mark.asyncio
async def test_pause_session_persists_paused_status(service, repo):
    session = await service.create_session()
    await service.pause_session()
    persisted = await repo.get_session_by_id(session.id)
    assert persisted.status == SessionStatus.PAUSED


@pytest.mark.asyncio
async def test_pause_session_emits_audit_event(service, repo):
    await service.create_session()
    await service.pause_session()
    count = await _count_audit_events(repo, "session_paused")
    assert count == 1


@pytest.mark.asyncio
async def test_pause_session_raises_when_already_paused(service):
    await service.create_session()
    await service.pause_session()
    with pytest.raises(InvalidTransitionError):
        await service.pause_session()


@pytest.mark.asyncio
async def test_pause_session_raises_when_finished(service):
    finished_session = Session.new()
    finished_session.status = SessionStatus.FINISHED
    service._current = finished_session
    with pytest.raises(InvalidTransitionError):
        await service.pause_session()


@pytest.mark.asyncio
async def test_pause_session_raises_when_no_session(service):
    with pytest.raises(InvalidTransitionError):
        await service.pause_session()


# ---------------------------------------------------------------------------
# resume_session tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resume_session_transitions_paused_to_active(service):
    await service.create_session()
    await service.pause_session()
    resumed = await service.resume_session()
    assert resumed.status == SessionStatus.ACTIVE


@pytest.mark.asyncio
async def test_resume_session_loads_from_db_when_no_in_memory_session(repo, mock_manager):
    """When no in-memory session exists, resume loads from DB."""
    # Populate DB with a paused session directly via repo.
    paused_session = Session.new()
    paused_session.status = SessionStatus.PAUSED
    await repo.upsert_session(paused_session)

    # Create a fresh service with no in-memory session.
    svc = SessionService(repo=repo, manager=mock_manager)
    resumed = await svc.resume_session()
    assert resumed.status == SessionStatus.ACTIVE
    assert resumed.id == paused_session.id


@pytest.mark.asyncio
async def test_resume_session_raises_when_already_active(service):
    await service.create_session()
    with pytest.raises(ActiveSessionExistsError):
        await service.resume_session()


@pytest.mark.asyncio
async def test_resume_session_raises_when_no_resumable_session_in_db(service):
    # No session created — nothing in DB or memory.
    with pytest.raises(SessionNotFoundError):
        await service.resume_session()


@pytest.mark.asyncio
async def test_resume_session_raises_when_in_memory_session_is_finished(service):
    finished_session = Session.new()
    finished_session.status = SessionStatus.FINISHED
    service._current = finished_session
    with pytest.raises(InvalidTransitionError):
        await service.resume_session()


# ---------------------------------------------------------------------------
# finish_session tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_finish_session_transitions_active_to_finished(service, repo):
    session = await service.create_session()
    await service.finish_session()
    persisted = await repo.get_session_by_id(session.id)
    assert persisted.status == SessionStatus.FINISHED


@pytest.mark.asyncio
async def test_finish_session_transitions_paused_to_finished(service, repo):
    session = await service.create_session()
    await service.pause_session()
    await service.finish_session()
    persisted = await repo.get_session_by_id(session.id)
    assert persisted.status == SessionStatus.FINISHED


@pytest.mark.asyncio
async def test_finish_session_creates_and_persists_archive(service, repo):
    session = await service.create_session()
    await service.finish_session()
    archive = await repo.get_archive_by_session_id(session.id)
    assert archive is not None
    assert archive.session_id == session.id


@pytest.mark.asyncio
async def test_finish_session_clears_in_memory_reference(service):
    await service.create_session()
    await service.finish_session()
    assert service.current_session is None


@pytest.mark.asyncio
async def test_finish_session_emits_finish_initiated_and_finished_audit_events(
    service, repo
):
    await service.create_session()
    await service.finish_session()
    initiated = await _count_audit_events(repo, "session_finish_initiated")
    finished = await _count_audit_events(repo, "session_finished")
    assert initiated == 1
    assert finished == 1


@pytest.mark.asyncio
async def test_finish_session_raises_when_no_session(service):
    with pytest.raises(InvalidTransitionError):
        await service.finish_session()


@pytest.mark.asyncio
async def test_finish_session_raises_when_already_finished(service):
    finished_session = Session.new()
    finished_session.status = SessionStatus.FINISHED
    service._current = finished_session
    with pytest.raises(InvalidTransitionError):
        await service.finish_session()


@pytest.mark.asyncio
async def test_finish_session_raises_archive_error_and_does_not_mark_finished(
    service, repo, mock_manager
):
    """If archive persistence fails, session must NOT be marked FINISHED."""
    session = await service.create_session()
    original_status = session.status

    # Patch repo.insert_archive to raise.
    async def _failing_insert_archive(_archive):
        raise RuntimeError("DB write failure")

    repo.insert_archive = _failing_insert_archive

    with pytest.raises(ArchiveError):
        await service.finish_session()

    # Session status must be unchanged in DB.
    persisted = await repo.get_session_by_id(session.id)
    assert persisted.status == original_status

    # Audit event for failure must exist.
    count = await _count_audit_events(repo, "session_finish_failed")
    assert count == 1


# ---------------------------------------------------------------------------
# Immutability tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_session_raises_after_finish(service):
    await service.create_session()
    await service.finish_session()
    # Force a finished session into memory to trigger the guard.
    finished_session = Session.new()
    finished_session.status = SessionStatus.FINISHED
    service._current = finished_session
    with pytest.raises(InvalidTransitionError):
        await service.save_session()


@pytest.mark.asyncio
async def test_pause_session_raises_after_finish(service):
    await service.create_session()
    await service.finish_session()
    finished_session = Session.new()
    finished_session.status = SessionStatus.FINISHED
    service._current = finished_session
    with pytest.raises(InvalidTransitionError):
        await service.pause_session()


# ---------------------------------------------------------------------------
# Summary tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_summary_returns_none_when_no_session(service):
    summary = service.get_summary()
    assert summary == {"session": None}


@pytest.mark.asyncio
async def test_get_summary_returns_correct_fields(service):
    session = await service.create_session()
    summary = service.get_summary()
    assert summary["session_id"] == session.id
    assert summary["status"] == SessionStatus.ACTIVE
    assert summary["active_game"] is None
    assert summary["player_list"] == []
    assert summary["standings"] == []


@pytest.mark.asyncio
async def test_get_summary_reflects_active_game_and_players(service):
    session = await service.create_session()
    session.active_game = "ohms_law"
    session.players = [{"id": "p1", "name": "Alice"}]
    session.standings = [{"player_id": "p1", "score": 100}]

    summary = service.get_summary()
    assert summary["active_game"] == "ohms_law"
    assert summary["player_list"] == [{"id": "p1", "name": "Alice"}]
    assert summary["standings"] == [{"player_id": "p1", "score": 100}]
