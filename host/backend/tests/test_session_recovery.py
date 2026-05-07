"""
Tests for the startup recovery scanner (EP-02, US-03).
SRS reference: FR-009, Section 13.3, NFR-007–NFR-010, AC-009.

Coverage:
- US-03 AC-1: after restart, system restores the latest consistent saved session
- US-03 AC-2: recovery distinguishes resumable sessions from finished archives
- US-03 AC-3: corrupt/incomplete saves handled without crashing
- US-03 AC-4: recovery outcome is logged and operator-visible (RecoveryResult)
"""

import datetime
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from ee_game_backend.session.database import open_database
from ee_game_backend.session.models import Session, SessionStatus
from ee_game_backend.session.recovery import RecoveryResult, run_recovery
from ee_game_backend.session.repository import SessionRepository
from ee_game_backend.session.service import SessionService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db():
    """Fresh in-memory SQLite database for each test."""
    conn = await open_database(":memory:")
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def repo(db):
    """Real SessionRepository backed by the in-memory database."""
    return SessionRepository(db)


@pytest.fixture
def mock_manager():
    """Mock ConnectionManager so SessionService does not need real WebSockets."""
    manager = MagicMock()
    manager.broadcast_to_frontends = AsyncMock()
    return manager


@pytest_asyncio.fixture
async def service(repo, mock_manager):
    """Real SessionService with a mocked ConnectionManager."""
    return SessionService(repo=repo, manager=mock_manager)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _insert_corrupt_session(db, session_id: str, status: str = "active") -> None:
    """
    Insert a session row with a deliberately wrong checksum to simulate corruption.
    """
    now = datetime.datetime.now(datetime.UTC).isoformat()
    payload = json.dumps(
        {
            "id": session_id,
            "status": status,
            "created_at": now,
            "updated_at": now,
            "current_round_id": None,
            "players": [],
            "standings": [],
            "active_game": None,
        },
        sort_keys=True,
    )
    bad_checksum = "deadbeef" * 8  # 64 hex chars, but wrong
    await db.execute(
        """
        INSERT INTO sessions (id, status, created_at, updated_at, session_payload, checksum)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (session_id, status, now, now, payload, bad_checksum),
    )
    await db.commit()


# ---------------------------------------------------------------------------
# No session in DB
# ---------------------------------------------------------------------------


async def test_no_session_returns_not_recovered(repo, service):
    """With an empty database, run_recovery returns recovered=False."""
    result = await run_recovery(repo, service)

    assert isinstance(result, RecoveryResult)
    assert result.recovered is False
    assert result.session_id is None
    assert result.session_status is None


async def test_no_session_does_not_call_restore(repo, mock_manager):
    """When no session exists, restore_session must never be called."""
    service = SessionService(repo=repo, manager=mock_manager)
    service.restore_session = MagicMock(wraps=service.restore_session)

    await run_recovery(repo, service)

    service.restore_session.assert_not_called()


# ---------------------------------------------------------------------------
# ACTIVE session in DB
# ---------------------------------------------------------------------------


async def test_active_session_recovered(repo, service):
    """A persisted ACTIVE session is restored and result reflects that."""
    session = Session.new()  # status=ACTIVE by default
    await repo.upsert_session(session)

    result = await run_recovery(repo, service)

    assert result.recovered is True
    assert result.session_id == session.id
    assert result.session_status == SessionStatus.ACTIVE


async def test_active_session_restore_called_with_correct_session(repo, mock_manager):
    """restore_session is called with the exact Session object that was persisted."""
    service = SessionService(repo=repo, manager=mock_manager)
    service.restore_session = MagicMock(wraps=service.restore_session)

    session = Session.new()
    await repo.upsert_session(session)

    await run_recovery(repo, service)

    service.restore_session.assert_called_once()
    restored = service.restore_session.call_args[0][0]
    assert restored.id == session.id


async def test_active_session_sets_current_session(repo, service):
    """After recovery, service.current_session is not None."""
    session = Session.new()
    await repo.upsert_session(session)

    await run_recovery(repo, service)

    assert service.current_session is not None


async def test_active_session_current_session_status_is_active(repo, service):
    """After recovery of an ACTIVE session, current_session.status is ACTIVE."""
    session = Session.new()
    await repo.upsert_session(session)

    await run_recovery(repo, service)

    assert service.current_session.status == SessionStatus.ACTIVE


# ---------------------------------------------------------------------------
# PAUSED session in DB
# ---------------------------------------------------------------------------


async def test_paused_session_recovered(repo, service):
    """A persisted PAUSED session is restored and result reflects that."""
    session = Session.new()
    session.status = SessionStatus.PAUSED
    await repo.upsert_session(session)

    result = await run_recovery(repo, service)

    assert result.recovered is True
    assert result.session_id == session.id
    assert result.session_status == SessionStatus.PAUSED


async def test_paused_session_restore_called(repo, mock_manager):
    """restore_session is invoked when a PAUSED session is found."""
    service = SessionService(repo=repo, manager=mock_manager)
    service.restore_session = MagicMock(wraps=service.restore_session)

    session = Session.new()
    session.status = SessionStatus.PAUSED
    await repo.upsert_session(session)

    await run_recovery(repo, service)

    service.restore_session.assert_called_once()


async def test_paused_session_current_session_status_is_paused(repo, service):
    """After recovery of a PAUSED session, current_session.status is PAUSED."""
    session = Session.new()
    session.status = SessionStatus.PAUSED
    await repo.upsert_session(session)

    await run_recovery(repo, service)

    assert service.current_session is not None
    assert service.current_session.status == SessionStatus.PAUSED


async def test_paused_session_message_mentions_resume(repo, service):
    """The recovery message for a PAUSED session references the resume endpoint."""
    session = Session.new()
    session.status = SessionStatus.PAUSED
    await repo.upsert_session(session)

    result = await run_recovery(repo, service)

    assert "resume" in result.message.lower()


# ---------------------------------------------------------------------------
# FINISHED session only in DB — must NOT be resumed
# ---------------------------------------------------------------------------


async def test_finished_session_only_returns_not_recovered(repo, service):
    """A FINISHED session is never treated as a resumable candidate."""
    session = Session.new()
    session.status = SessionStatus.FINISHED
    await repo.upsert_session(session)

    result = await run_recovery(repo, service)

    assert result.recovered is False


async def test_finished_session_restore_not_called(repo, mock_manager):
    """restore_session is NOT called when only a FINISHED session exists."""
    service = SessionService(repo=repo, manager=mock_manager)
    service.restore_session = MagicMock(wraps=service.restore_session)

    session = Session.new()
    session.status = SessionStatus.FINISHED
    await repo.upsert_session(session)

    await run_recovery(repo, service)

    service.restore_session.assert_not_called()


# ---------------------------------------------------------------------------
# Corrupt row + valid row — valid one wins
# ---------------------------------------------------------------------------


async def test_corrupt_row_skipped_valid_row_restored(db, repo, service):
    """When a corrupt row precedes a valid row, the valid row is recovered."""
    # Insert a corrupt active session (will sort first by updated_at if same time,
    # but we insert the valid one afterward with a slightly later timestamp).
    await _insert_corrupt_session(db, "corrupt-session-id", status="active")

    # Valid session inserted after; has a newer updated_at automatically via Session.new().
    valid_session = Session.new()
    await repo.upsert_session(valid_session)

    result = await run_recovery(repo, service)

    assert result.recovered is True
    assert result.session_id == valid_session.id


async def test_corrupt_row_skipped_does_not_crash(db, repo, service):
    """run_recovery does not raise when a corrupt row is encountered."""
    await _insert_corrupt_session(db, "only-corrupt-id", status="active")

    result = await run_recovery(repo, service)

    # Either no valid session or the corrupt one is skipped — just must not raise.
    assert result.recovered is False


# ---------------------------------------------------------------------------
# All corrupt rows
# ---------------------------------------------------------------------------


async def test_all_corrupt_rows_returns_not_recovered(db, repo, service):
    """When every row is corrupt, recovered=False and no exception is raised."""
    await _insert_corrupt_session(db, "corrupt-1")
    await _insert_corrupt_session(db, "corrupt-2")

    result = await run_recovery(repo, service)

    assert result.recovered is False
    assert result.session_id is None


async def test_all_corrupt_rows_restore_not_called(db, repo, mock_manager):
    """restore_session is NOT called when all rows are corrupt."""
    service = SessionService(repo=repo, manager=mock_manager)
    service.restore_session = MagicMock(wraps=service.restore_session)

    await _insert_corrupt_session(db, "corrupt-only")

    await run_recovery(repo, service)

    service.restore_session.assert_not_called()


# ---------------------------------------------------------------------------
# DB scan exception
# ---------------------------------------------------------------------------


async def test_db_exception_returns_not_recovered(repo, service):
    """If repo.get_latest_resumable_session() raises, run_recovery returns recovered=False."""
    repo.get_latest_resumable_session = AsyncMock(side_effect=RuntimeError("DB exploded"))

    result = await run_recovery(repo, service)

    assert result.recovered is False
    assert result.session_id is None


async def test_db_exception_does_not_propagate(repo, service):
    """run_recovery never raises — it swallows the exception and returns a safe result."""
    repo.get_latest_resumable_session = AsyncMock(side_effect=Exception("unexpected"))

    # Must not raise:
    result = await run_recovery(repo, service)

    assert isinstance(result, RecoveryResult)
    assert result.recovered is False


async def test_db_exception_restore_not_called(repo, mock_manager):
    """restore_session is NOT called when the DB scan raises."""
    service = SessionService(repo=repo, manager=mock_manager)
    service.restore_session = MagicMock(wraps=service.restore_session)
    repo.get_latest_resumable_session = AsyncMock(side_effect=RuntimeError("boom"))

    await run_recovery(repo, service)

    service.restore_session.assert_not_called()


# ---------------------------------------------------------------------------
# Multiple sessions — most recently updated wins
# ---------------------------------------------------------------------------


async def test_most_recent_session_is_recovered(repo, service):
    """With two ACTIVE sessions, the more recently updated one is restored."""
    older = Session.new()
    older.updated_at = datetime.datetime(2024, 1, 1, 12, 0, 0)
    await repo.upsert_session(older)

    newer = Session.new()
    newer.updated_at = datetime.datetime(2024, 6, 1, 12, 0, 0)
    await repo.upsert_session(newer)

    result = await run_recovery(repo, service)

    assert result.recovered is True
    assert result.session_id == newer.id


async def test_most_recent_paused_beats_older_active(repo, service):
    """The most recently updated session wins regardless of ACTIVE vs PAUSED status."""
    older_active = Session.new()
    older_active.updated_at = datetime.datetime(2024, 1, 1, 0, 0, 0)
    await repo.upsert_session(older_active)

    newer_paused = Session.new()
    newer_paused.status = SessionStatus.PAUSED
    newer_paused.updated_at = datetime.datetime(2024, 12, 1, 0, 0, 0)
    await repo.upsert_session(newer_paused)

    result = await run_recovery(repo, service)

    assert result.recovered is True
    assert result.session_id == newer_paused.id
    assert result.session_status == SessionStatus.PAUSED
