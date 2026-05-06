"""
SQLite migration runner for the EE-Game persistence layer.

The project intentionally keeps SQLite DDL close to the repository so classroom
deployments can recover without an external migration tool.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 2

_BASE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,
    status          TEXT NOT NULL CHECK(status IN ('active', 'paused', 'finished')),
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    session_payload TEXT NOT NULL,
    checksum        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_archives (
    id                  TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    finished_at         TEXT NOT NULL,
    anonymised_payload  TEXT NOT NULL,
    retention_state     TEXT NOT NULL DEFAULT 'retained'
);

CREATE TABLE IF NOT EXISTS audit_events (
    id              TEXT PRIMARY KEY,
    session_id      TEXT,
    action_type     TEXT NOT NULL,
    actor_type      TEXT NOT NULL DEFAULT 'host',
    payload_summary TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL
);
"""

_V2_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS rounds (
    id                  TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    game_id             TEXT NOT NULL,
    phase               TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    started_at          TEXT,
    ended_at            TEXT,
    timer_total_ms      INTEGER NOT NULL DEFAULT 0,
    timer_remaining_ms  INTEGER NOT NULL DEFAULT 0,
    round_payload       TEXT NOT NULL,
    checksum            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS round_events (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    round_id        TEXT NOT NULL,
    player_id       TEXT,
    device_id       TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    phase           TEXT NOT NULL,
    dedupe_key      TEXT,
    event_payload   TEXT NOT NULL,
    received_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS score_events (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    round_id        TEXT NOT NULL,
    player_id       TEXT,
    team_id         TEXT,
    score_delta     INTEGER NOT NULL,
    reason          TEXT NOT NULL,
    source          TEXT NOT NULL,
    payload         TEXT NOT NULL DEFAULT '{}',
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS team_assignments (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    round_id        TEXT NOT NULL,
    team_id         TEXT NOT NULL,
    team_name       TEXT NOT NULL,
    player_id       TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_status_updated
    ON sessions(status, updated_at);

CREATE INDEX IF NOT EXISTS idx_archives_finished_retention
    ON session_archives(retention_state, finished_at);

CREATE INDEX IF NOT EXISTS idx_audit_session_created
    ON audit_events(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_rounds_session_updated
    ON rounds(session_id, updated_at);

CREATE INDEX IF NOT EXISTS idx_round_events_round_received
    ON round_events(round_id, received_at);

CREATE INDEX IF NOT EXISTS idx_round_events_dedupe
    ON round_events(round_id, dedupe_key)
    WHERE dedupe_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_score_events_session_player
    ON score_events(session_id, player_id, created_at);

CREATE INDEX IF NOT EXISTS idx_score_events_round_team
    ON score_events(round_id, team_id);

CREATE INDEX IF NOT EXISTS idx_team_assignments_round_team
    ON team_assignments(round_id, team_id);
"""


async def apply_migrations(db: Any) -> int:
    """Apply all known migrations and return the resulting schema version."""
    await db.executescript(_BASE_SCHEMA_SQL)
    version = await _get_schema_version(db)
    if version == 0:
        version = 1
        await _record_schema_version(db, version)

    if version < 2:
        await db.executescript(_V2_SCHEMA_SQL)
        version = 2
        await _record_schema_version(db, version)
        logger.info("SQLite schema migrated to version %d", version)
    else:
        await db.executescript(_V2_SCHEMA_SQL)

    await db.commit()
    return version


async def _get_schema_version(db: Any) -> int:
    async with db.execute("SELECT MAX(version) AS version FROM schema_version") as cursor:
        row = await cursor.fetchone()
    if row is None or row["version"] is None:
        return 0
    return int(row["version"])


async def _record_schema_version(db: Any, version: int) -> None:
    await db.execute(
        """
        INSERT OR IGNORE INTO schema_version (version, applied_at)
        VALUES (?, ?)
        """,
        (version, datetime.datetime.utcnow().isoformat()),
    )
