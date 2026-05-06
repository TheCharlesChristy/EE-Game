"""
Integration tests for EP-02 SessionRepository using an in-memory SQLite database.
SRS reference: FR-001–FR-010, Section 9.1–9.4, NFR-007, NFR-008.
"""

import datetime
import json

import pytest

from ee_game_backend.session.database import open_database
from ee_game_backend.session.models import (
    AuditEvent,
    Session,
    SessionArchive,
    SessionStatus,
)
from ee_game_backend.session.repository import SessionRepository


@pytest.fixture
async def db():
    """Open an in-memory SQLite database with the full schema applied."""
    conn = await open_database(":memory:")
    yield conn
    await conn.close()


@pytest.fixture
async def repo(db):
    """Provide a SessionRepository backed by the in-memory database."""
    return SessionRepository(db)


# ---------------------------------------------------------------------------
# upsert_session — insert
# ---------------------------------------------------------------------------


async def test_upsert_session_inserts_new_session(repo):
    session = Session.new()
    await repo.upsert_session(session)

    result = await repo.get_session_by_id(session.id)
    assert result is not None
    assert result.id == session.id


# ---------------------------------------------------------------------------
# upsert_session — update (same id)
# ---------------------------------------------------------------------------


async def test_upsert_session_updates_existing_session(repo):
    session = Session.new()
    await repo.upsert_session(session)

    session.status = SessionStatus.PAUSED
    session.updated_at = datetime.datetime.utcnow()
    await repo.upsert_session(session)

    result = await repo.get_session_by_id(session.id)
    assert result is not None
    assert result.status == SessionStatus.PAUSED


# ---------------------------------------------------------------------------
# get_session_by_id
# ---------------------------------------------------------------------------


async def test_get_session_by_id_returns_correct_session(repo):
    session = Session.new()
    session.active_game = "resistor_colour_code"
    await repo.upsert_session(session)

    result = await repo.get_session_by_id(session.id)
    assert result is not None
    assert result.id == session.id
    assert result.active_game == "resistor_colour_code"
    assert result.status == SessionStatus.ACTIVE


async def test_get_session_by_id_returns_none_for_unknown_id(repo):
    result = await repo.get_session_by_id("does-not-exist")
    assert result is None


# ---------------------------------------------------------------------------
# get_latest_resumable_session
# ---------------------------------------------------------------------------


async def test_get_latest_resumable_session_returns_none_when_empty(repo):
    result = await repo.get_latest_resumable_session()
    assert result is None


async def test_get_latest_resumable_session_returns_active_session(repo):
    session = Session.new()
    await repo.upsert_session(session)

    result = await repo.get_latest_resumable_session()
    assert result is not None
    assert result.id == session.id


async def test_get_latest_resumable_session_returns_paused_session(repo):
    session = Session.new()
    session.status = SessionStatus.PAUSED
    await repo.upsert_session(session)

    result = await repo.get_latest_resumable_session()
    assert result is not None
    assert result.id == session.id


async def test_get_latest_resumable_session_skips_finished_sessions(repo):
    session = Session.new()
    session.status = SessionStatus.FINISHED
    await repo.upsert_session(session)

    result = await repo.get_latest_resumable_session()
    assert result is None


async def test_get_latest_resumable_session_returns_most_recently_updated(repo, db):
    older = Session.new()
    older.updated_at = datetime.datetime(2026, 1, 1, 12, 0, 0)
    await repo.upsert_session(older)

    newer = Session.new()
    newer.updated_at = datetime.datetime(2026, 1, 2, 12, 0, 0)
    await repo.upsert_session(newer)

    result = await repo.get_latest_resumable_session()
    assert result is not None
    assert result.id == newer.id


async def test_get_latest_resumable_session_skips_corrupt_rows_returns_next(repo, db):
    """
    Insert one corrupt row (bad checksum) and one valid row.
    The repository must skip the corrupt row and return the valid one.
    NFR-008: corrupt rows must not crash recovery.
    """
    # Insert a valid session that will rank second by updated_at.
    good_session = Session.new()
    good_session.updated_at = datetime.datetime(2026, 1, 1, 12, 0, 0)
    await repo.upsert_session(good_session)

    # Manually insert a corrupt row that ranks first by updated_at.
    corrupt_id = "corrupt-session-id"
    payload = json.dumps({"id": corrupt_id, "status": "active"})
    bad_checksum = "0" * 64  # Deliberately wrong checksum.
    await db.execute(
        """
        INSERT INTO sessions (id, status, created_at, updated_at, session_payload, checksum)
        VALUES (?, 'active', '2026-01-02T12:00:00', '2026-01-02T12:00:00', ?, ?)
        """,
        (corrupt_id, payload, bad_checksum),
    )
    await db.commit()

    result = await repo.get_latest_resumable_session()
    assert result is not None
    assert result.id == good_session.id


# ---------------------------------------------------------------------------
# count_non_finished_sessions
# ---------------------------------------------------------------------------


async def test_count_non_finished_sessions_when_empty(repo):
    count = await repo.count_non_finished_sessions()
    assert count == 0


async def test_count_non_finished_sessions_counts_active_and_paused(repo):
    active = Session.new()
    await repo.upsert_session(active)

    paused = Session.new()
    paused.status = SessionStatus.PAUSED
    await repo.upsert_session(paused)

    finished = Session.new()
    finished.status = SessionStatus.FINISHED
    await repo.upsert_session(finished)

    count = await repo.count_non_finished_sessions()
    assert count == 2


# ---------------------------------------------------------------------------
# insert_archive / get_archive_by_session_id
# ---------------------------------------------------------------------------


async def test_insert_archive_persists_row(repo):
    session = Session.new()
    session.status = SessionStatus.FINISHED
    archive = SessionArchive.from_session(session)

    await repo.insert_archive(archive)

    result = await repo.get_archive_by_session_id(session.id)
    assert result is not None
    assert result.session_id == session.id


async def test_get_archive_by_session_id_returns_correct_archive(repo):
    session = Session.new()
    session.players = [{"name": "X", "colour": "green", "cumulative_score": 99}]
    session.status = SessionStatus.FINISHED
    archive = SessionArchive.from_session(session)

    await repo.insert_archive(archive)

    result = await repo.get_archive_by_session_id(session.id)
    assert result is not None
    assert result.id == archive.id
    assert result.retention_state == "retained"
    players = result.anonymised_payload["players"]
    assert len(players) == 1
    assert players[0]["archive_label"] == "Player_1"
    assert players[0]["cumulative_score"] == 99


async def test_get_archive_by_session_id_returns_none_for_unknown(repo):
    result = await repo.get_archive_by_session_id("not-a-real-session-id")
    assert result is None


# ---------------------------------------------------------------------------
# insert_audit_event
# ---------------------------------------------------------------------------


async def test_insert_audit_event_persists_without_raising(repo, db):
    event = AuditEvent.new(
        session_id="some-session",
        action_type="session_created",
        payload_summary="new session",
    )
    # Must not raise.
    await repo.insert_audit_event(event)

    # Verify it made it into the database.
    async with db.execute(
        "SELECT * FROM audit_events WHERE id = ?", (event.id,)
    ) as cursor:
        row = await cursor.fetchone()

    assert row is not None
    assert row["action_type"] == "session_created"
    assert row["actor_type"] == "host"
    assert row["session_id"] == "some-session"


async def test_insert_audit_event_with_none_session_id(repo, db):
    event = AuditEvent.new(session_id=None, action_type="system_restart")
    await repo.insert_audit_event(event)

    async with db.execute(
        "SELECT session_id FROM audit_events WHERE id = ?", (event.id,)
    ) as cursor:
        row = await cursor.fetchone()

    assert row is not None
    assert row["session_id"] is None
