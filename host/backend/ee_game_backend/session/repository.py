"""
SessionRepository: SQLite persistence for sessions, archives, and audit events.
SRS reference: FR-001–FR-010, Section 9.1–9.4, NFR-007, NFR-008.
"""

import datetime
import json
import logging
from typing import Any, Optional

from .models import AuditEvent, Session, SessionArchive, compute_checksum

logger = logging.getLogger(__name__)


class SessionRepository:
    """
    Thin repository layer over the sessions, session_archives, and audit_events tables.
    All methods are async and safe to call from the FastAPI event loop.
    """

    def __init__(self, db: Any) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Session CRUD
    # ------------------------------------------------------------------

    async def upsert_session(self, session: Session) -> None:
        """
        Insert or replace the session record in the database.
        Computes a checksum for corruption detection (NFR-008).
        """
        payload_dict = session.to_payload_dict()
        payload_json = json.dumps(payload_dict, sort_keys=True)
        checksum = compute_checksum(payload_json)

        await self._db.execute(
            """
            INSERT INTO sessions (id, status, created_at, updated_at, session_payload, checksum)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status          = excluded.status,
                updated_at      = excluded.updated_at,
                session_payload = excluded.session_payload,
                checksum        = excluded.checksum
            """,
            (
                session.id,
                session.status,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                payload_json,
                checksum,
            ),
        )
        await self._db.commit()

    async def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Load and validate a session by ID. Returns None if not found or checksum fails."""
        async with self._db.execute(
            "SELECT session_payload, checksum FROM sessions WHERE id = ?",
            (session_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return None

        return self._deserialise_row(row["session_payload"], row["checksum"], session_id)

    async def get_latest_resumable_session(self) -> Optional[Session]:
        """
        Return the most recently updated non-FINISHED session with a valid checksum.
        Used for restart recovery (FR-009, NFR-007).
        Corrupt or incomplete rows are skipped with a warning log.
        """
        async with self._db.execute(
            """
            SELECT session_payload, checksum, id
            FROM sessions
            WHERE status IN ('active', 'paused')
            ORDER BY updated_at DESC
            """,
        ) as cursor:
            rows = await cursor.fetchall()

        for row in rows:
            session = self._deserialise_row(row["session_payload"], row["checksum"], row["id"])
            if session is not None:
                return session
            # Corrupt row already warned inside _deserialise_row.

        return None

    async def count_non_finished_sessions(self) -> int:
        """Count sessions with status ACTIVE or PAUSED."""
        async with self._db.execute(
            "SELECT COUNT(*) AS cnt FROM sessions WHERE status IN ('active', 'paused')"
        ) as cursor:
            row = await cursor.fetchone()
        return row["cnt"] if row else 0

    async def get_schema_version(self) -> int:
        """Return the current persistence schema version."""
        async with self._db.execute("SELECT MAX(version) AS version FROM schema_version") as cursor:
            row = await cursor.fetchone()
        return int(row["version"] or 0) if row else 0

    # ------------------------------------------------------------------
    # Archive
    # ------------------------------------------------------------------

    async def insert_archive(self, archive: SessionArchive) -> None:
        """Persist an immutable session archive (created on finish)."""
        payload_json = json.dumps(archive.anonymised_payload, sort_keys=True)
        await self._db.execute(
            """
            INSERT INTO session_archives (id, session_id, finished_at, anonymised_payload, retention_state)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                archive.id,
                archive.session_id,
                archive.finished_at.isoformat(),
                payload_json,
                archive.retention_state,
            ),
        )
        await self._db.commit()

    async def get_archive_by_session_id(self, session_id: str) -> Optional[SessionArchive]:
        """Load an archive record by session_id."""
        async with self._db.execute(
            "SELECT * FROM session_archives WHERE session_id = ?",
            (session_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return None

        return SessionArchive(
            id=row["id"],
            session_id=row["session_id"],
            finished_at=datetime.datetime.fromisoformat(row["finished_at"]),
            anonymised_payload=json.loads(row["anonymised_payload"]),
            retention_state=row["retention_state"],
        )

    async def expire_archives_before(self, cutoff: datetime.datetime) -> int:
        """Mark retained archives older than cutoff as expired and return affected rows."""
        cursor = await self._db.execute(
            """
            UPDATE session_archives
            SET retention_state = 'expired'
            WHERE retention_state = 'retained' AND finished_at < ?
            """,
            (cutoff.isoformat(),),
        )
        await self._db.commit()
        return cursor.rowcount

    # ------------------------------------------------------------------
    # Audit events
    # ------------------------------------------------------------------

    async def insert_audit_event(self, event: AuditEvent) -> None:
        """Persist an audit event. Never raises — logs on error."""
        try:
            await self._db.execute(
                """
                INSERT INTO audit_events (id, session_id, action_type, actor_type, payload_summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.session_id,
                    event.action_type,
                    event.actor_type,
                    event.payload_summary,
                    event.created_at.isoformat(),
                ),
            )
            await self._db.commit()
        except Exception:
            logger.error(
                "Failed to persist audit event action_type=%s session_id=%s",
                event.action_type,
                event.session_id,
                exc_info=True,
            )

    async def list_audit_events(self, session_id: str | None = None) -> list[dict[str, Any]]:
        """Return audit events, optionally filtered by session_id."""
        if session_id is None:
            sql = "SELECT * FROM audit_events ORDER BY created_at ASC"
            args: tuple[Any, ...] = ()
        else:
            sql = "SELECT * FROM audit_events WHERE session_id = ? ORDER BY created_at ASC"
            args = (session_id,)
        async with self._db.execute(sql, args) as cursor:
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Rounds
    # ------------------------------------------------------------------

    async def upsert_round(self, record: dict[str, Any]) -> None:
        """
        Insert or update a round state record.

        `round_payload` is checksummed for the same corruption-detection reason
        as session payloads.
        """
        payload = record.get("round_payload", {})
        payload_json = json.dumps(payload, sort_keys=True)
        checksum = compute_checksum(payload_json)
        await self._db.execute(
            """
            INSERT INTO rounds (
                id, session_id, game_id, phase, created_at, updated_at, started_at,
                ended_at, timer_total_ms, timer_remaining_ms, round_payload, checksum
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                phase              = excluded.phase,
                updated_at         = excluded.updated_at,
                started_at         = excluded.started_at,
                ended_at           = excluded.ended_at,
                timer_total_ms     = excluded.timer_total_ms,
                timer_remaining_ms = excluded.timer_remaining_ms,
                round_payload      = excluded.round_payload,
                checksum           = excluded.checksum
            """,
            (
                record["id"],
                record["session_id"],
                record["game_id"],
                record["phase"],
                self._iso(record["created_at"]),
                self._iso(record["updated_at"]),
                self._iso(record.get("started_at")),
                self._iso(record.get("ended_at")),
                int(record.get("timer_total_ms", 0)),
                int(record.get("timer_remaining_ms", 0)),
                payload_json,
                checksum,
            ),
        )
        await self._db.commit()

    async def get_round_by_id(self, round_id: str) -> dict[str, Any] | None:
        """Load a round record by id, returning None for missing or corrupt rows."""
        async with self._db.execute("SELECT * FROM rounds WHERE id = ?", (round_id,)) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        payload_json = row["round_payload"]
        if compute_checksum(payload_json) != row["checksum"]:
            logger.warning("Checksum mismatch for round_id=%s — skipping corrupt row", round_id)
            return None
        record = dict(row)
        record["round_payload"] = json.loads(payload_json)
        return record

    async def list_rounds(self, session_id: str) -> list[dict[str, Any]]:
        """Return all rounds for a session, newest last."""
        async with self._db.execute(
            """
            SELECT * FROM rounds
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        records: list[dict[str, Any]] = []
        for row in rows:
            payload_json = row["round_payload"]
            if compute_checksum(payload_json) != row["checksum"]:
                logger.warning("Checksum mismatch for round_id=%s in list_rounds", row["id"])
                continue
            record = dict(row)
            record["round_payload"] = json.loads(payload_json)
            records.append(record)
        return records

    # ------------------------------------------------------------------
    # Round events
    # ------------------------------------------------------------------

    async def insert_round_event(self, event: dict[str, Any]) -> None:
        """Persist one raw device event for the active round."""
        payload_json = json.dumps(event.get("event_payload", {}), sort_keys=True)
        await self._db.execute(
            """
            INSERT INTO round_events (
                id, session_id, round_id, player_id, device_id, event_type,
                phase, dedupe_key, event_payload, received_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"],
                event["session_id"],
                event["round_id"],
                event.get("player_id"),
                event["device_id"],
                event["event_type"],
                event["phase"],
                event.get("dedupe_key"),
                payload_json,
                self._iso(event["received_at"]),
            ),
        )
        await self._db.commit()

    async def has_round_event_dedupe_key(self, round_id: str, dedupe_key: str) -> bool:
        """Return True if an event with this dedupe key already exists."""
        async with self._db.execute(
            """
            SELECT 1 FROM round_events
            WHERE round_id = ? AND dedupe_key = ?
            LIMIT 1
            """,
            (round_id, dedupe_key),
        ) as cursor:
            row = await cursor.fetchone()
        return row is not None

    async def list_round_events(self, round_id: str) -> list[dict[str, Any]]:
        """Return raw events for a round in arrival order."""
        async with self._db.execute(
            """
            SELECT * FROM round_events
            WHERE round_id = ?
            ORDER BY received_at ASC
            """,
            (round_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            record = dict(row)
            record["event_payload"] = json.loads(record["event_payload"])
            events.append(record)
        return events

    # ------------------------------------------------------------------
    # Score events
    # ------------------------------------------------------------------

    async def insert_score_events(self, events: list[dict[str, Any]]) -> None:
        """Persist score deltas. Empty lists are a no-op."""
        if not events:
            return
        await self._db.executemany(
            """
            INSERT INTO score_events (
                id, session_id, round_id, player_id, team_id, score_delta,
                reason, source, payload, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    event["id"],
                    event["session_id"],
                    event["round_id"],
                    event.get("player_id"),
                    event.get("team_id"),
                    int(event["score_delta"]),
                    event["reason"],
                    event["source"],
                    json.dumps(event.get("payload", {}), sort_keys=True),
                    self._iso(event["created_at"]),
                )
                for event in events
            ],
        )
        await self._db.commit()

    async def list_score_events(self, session_id: str) -> list[dict[str, Any]]:
        """Return all score events for a session."""
        async with self._db.execute(
            """
            SELECT * FROM score_events
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            record = dict(row)
            record["payload"] = json.loads(record["payload"])
            events.append(record)
        return events

    async def list_round_score_events(self, round_id: str) -> list[dict[str, Any]]:
        """Return score events for one round."""
        async with self._db.execute(
            """
            SELECT * FROM score_events
            WHERE round_id = ?
            ORDER BY created_at ASC
            """,
            (round_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        records = [dict(row) for row in rows]
        for record in records:
            record["payload"] = json.loads(record["payload"])
        return records

    # ------------------------------------------------------------------
    # Team assignments
    # ------------------------------------------------------------------

    async def replace_team_assignments(
        self,
        round_id: str,
        assignments: list[dict[str, Any]],
    ) -> None:
        """Replace the full set of team assignments for one round."""
        await self._db.execute("DELETE FROM team_assignments WHERE round_id = ?", (round_id,))
        if assignments:
            await self._db.executemany(
                """
                INSERT INTO team_assignments (
                    id, session_id, round_id, team_id, team_name, player_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item["id"],
                        item["session_id"],
                        item["round_id"],
                        item["team_id"],
                        item["team_name"],
                        item["player_id"],
                        self._iso(item["created_at"]),
                    )
                    for item in assignments
                ],
            )
        await self._db.commit()

    async def list_team_assignments(self, round_id: str) -> list[dict[str, Any]]:
        """Return team assignments for one round."""
        async with self._db.execute(
            """
            SELECT * FROM team_assignments
            WHERE round_id = ?
            ORDER BY team_id ASC, created_at ASC
            """,
            (round_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    async def get_table_counts(self) -> dict[str, int]:
        """Return row counts for all persistence tables used by diagnostics."""
        counts: dict[str, int] = {}
        for table in (
            "sessions",
            "session_archives",
            "audit_events",
            "rounds",
            "round_events",
            "score_events",
            "team_assignments",
        ):
            async with self._db.execute(f"SELECT COUNT(*) AS cnt FROM {table}") as cursor:
                row = await cursor.fetchone()
            counts[table] = int(row["cnt"] or 0) if row else 0
        return counts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _deserialise_row(
        payload_json: str,
        expected_checksum: str,
        session_id: str,
    ) -> Optional[Session]:
        """
        Parse payload JSON, verify checksum, and return a Session.
        Returns None if the checksum fails (corrupt row) or JSON is malformed.
        NFR-008: minimise risk of session corruption.
        """
        actual_checksum = compute_checksum(payload_json)
        if actual_checksum != expected_checksum:
            logger.warning(
                "Checksum mismatch for session_id=%s — skipping corrupt row",
                session_id,
            )
            return None

        try:
            data = json.loads(payload_json)
            return Session.from_payload_dict(data)
        except Exception:
            logger.warning(
                "Failed to deserialise session_id=%s — skipping",
                session_id,
                exc_info=True,
            )
            return None

    @staticmethod
    def _iso(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        return str(value)
