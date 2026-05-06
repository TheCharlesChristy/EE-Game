"""
SessionService: authoritative session lifecycle manager for EP-02.
SRS reference: FR-001–FR-010, Section 8.1, Section 14.3, AC-009, AC-010.
"""

import datetime
import logging
from typing import Optional

from ..core.connection_manager import ConnectionManager
from .exceptions import (
    ActiveSessionExistsError,
    ArchiveError,
    InvalidTransitionError,
    SessionNotFoundError,
)
from .models import AuditEvent, Session, SessionArchive, SessionStatus
from .repository import SessionRepository

logger = logging.getLogger(__name__)

# Audit action-type constants — keep as string literals to avoid a separate enum.
_ACTION_CREATED = "session_created"
_ACTION_SAVED = "session_saved"
_ACTION_PAUSED = "session_paused"
_ACTION_RESUMED = "session_resumed"
_ACTION_FINISH_INITIATED = "session_finish_initiated"
_ACTION_FINISHED = "session_finished"
_ACTION_FINISH_FAILED = "session_finish_failed"
_ACTION_BLOCKED_CONCURRENT = "session_create_blocked_concurrent"


class SessionService:
    """
    Manages the full session lifecycle: create, save, pause, resume, finish.

    Rules enforced here:
    - Only one non-FINISHED session may exist at a time (FR-010).
    - Save does not change the session's lifecycle status.
    - Pause transitions ACTIVE → PAUSED.
    - Resume transitions PAUSED → ACTIVE (or loads from DB if no in-memory session).
    - Finish transitions (ACTIVE | PAUSED) → FINISHED; immutability enforced after.
    - All transitions emit structured audit events (Section 14.3).
    - All transitions are broadcast to frontend clients via ConnectionManager.
    """

    def __init__(self, repo: SessionRepository, manager: ConnectionManager) -> None:
        self._repo = repo
        self._manager = manager
        self._current: Optional[Session] = None

    # ------------------------------------------------------------------
    # Read-only accessors
    # ------------------------------------------------------------------

    @property
    def current_session(self) -> Optional[Session]:
        """Return the in-memory current session, or None if no session is active."""
        return self._current

    # ------------------------------------------------------------------
    # Lifecycle commands
    # ------------------------------------------------------------------

    async def create_session(self) -> Session:
        """
        Create a new ACTIVE session.
        Raises ActiveSessionExistsError if a non-FINISHED session already exists.
        SRS: FR-001, FR-010.
        """
        if self._current is not None:
            logger.warning(
                "Blocked concurrent session creation; existing session_id=%s status=%s",
                self._current.id,
                self._current.status,
            )
            await self._repo.insert_audit_event(
                AuditEvent.new(
                    session_id=self._current.id,
                    action_type=_ACTION_BLOCKED_CONCURRENT,
                    payload_summary=f"blocked: existing session {self._current.id} is {self._current.status}",
                )
            )
            raise ActiveSessionExistsError(
                f"A session with id={self._current.id!r} and status={self._current.status!r} "
                "already exists. Finish or resume it before creating a new one."
            )

        session = Session.new()
        self._current = session

        await self._repo.upsert_session(session)
        await self._repo.insert_audit_event(
            AuditEvent.new(
                session_id=session.id,
                action_type=_ACTION_CREATED,
                payload_summary=f"session {session.id} created",
            )
        )
        await self._broadcast_session_update("session_created")
        logger.info("Session created: session_id=%s", session.id)
        return session

    async def save_session(self) -> Session:
        """
        Flush the current in-memory session state to SQLite without changing lifecycle status.
        Raises InvalidTransitionError if no session exists or the session is FINISHED.
        SRS: FR-003.
        """
        session = self._require_mutable_session("save")
        session.updated_at = datetime.datetime.utcnow()

        await self._repo.upsert_session(session)
        await self._repo.insert_audit_event(
            AuditEvent.new(
                session_id=session.id,
                action_type=_ACTION_SAVED,
                payload_summary=f"session {session.id} saved (status={session.status})",
            )
        )
        await self._broadcast_session_update("session_saved")
        logger.info("Session saved: session_id=%s status=%s", session.id, session.status)
        return session

    async def pause_session(self) -> Session:
        """
        Transition the current session from ACTIVE → PAUSED and persist.
        Raises InvalidTransitionError if session is not ACTIVE.
        SRS: FR-004.
        """
        session = self._require_mutable_session("pause")
        if session.status != SessionStatus.ACTIVE:
            raise InvalidTransitionError(
                f"Cannot pause session in status={session.status!r}. "
                "Session must be ACTIVE to pause."
            )

        session.status = SessionStatus.PAUSED
        session.updated_at = datetime.datetime.utcnow()

        await self._repo.upsert_session(session)
        await self._repo.insert_audit_event(
            AuditEvent.new(
                session_id=session.id,
                action_type=_ACTION_PAUSED,
                payload_summary=f"session {session.id} paused",
            )
        )
        await self._broadcast_session_update("session_paused")
        logger.info("Session paused: session_id=%s", session.id)
        return session

    async def resume_session(self) -> Session:
        """
        Resume the most recently saved non-FINISHED session.

        If the in-memory session is PAUSED, transitions it to ACTIVE.
        If no in-memory session exists, loads the latest resumable session from the DB.
        Raises ActiveSessionExistsError if the current in-memory session is already ACTIVE.
        Raises SessionNotFoundError if no resumable session can be found.
        SRS: FR-002, FR-009.
        """
        if self._current is not None and self._current.status == SessionStatus.ACTIVE:
            raise ActiveSessionExistsError(
                f"Session {self._current.id!r} is already ACTIVE. Cannot resume."
            )
        if self._current is not None and self._current.status == SessionStatus.FINISHED:
            raise InvalidTransitionError(
                f"Session {self._current.id!r} is FINISHED and cannot be resumed."
            )

        if self._current is not None and self._current.status == SessionStatus.PAUSED:
            # In-memory paused session — transition it to ACTIVE.
            session = self._current
        else:
            # No in-memory session — load from DB.
            session = await self._repo.get_latest_resumable_session()
            if session is None:
                raise SessionNotFoundError(
                    "No resumable session found. Create a new session instead."
                )
            self._current = session

        session.status = SessionStatus.ACTIVE
        session.updated_at = datetime.datetime.utcnow()

        await self._repo.upsert_session(session)
        await self._repo.insert_audit_event(
            AuditEvent.new(
                session_id=session.id,
                action_type=_ACTION_RESUMED,
                payload_summary=f"session {session.id} resumed",
            )
        )
        await self._broadcast_session_update("session_resumed")
        logger.info("Session resumed: session_id=%s", session.id)
        return session

    async def finish_session(self) -> SessionArchive:
        """
        Permanently finish the current session.

        Transitions (ACTIVE | PAUSED) → FINISHED, creates an anonymised archive,
        and clears the in-memory session reference so it cannot be mutated further.
        Raises InvalidTransitionError if no current session or session is already FINISHED.
        Raises ArchiveError if archive persistence fails (session remains in previous state).
        SRS: FR-005, FR-006, FR-007, Section 14.3.

        NOTE: The caller (API layer) must verify that the host provided explicit
        confirmation before calling this method. This method does not enforce
        confirmation — it relies on the API layer to do so.
        """
        session = self._require_mutable_session("finish")

        await self._repo.insert_audit_event(
            AuditEvent.new(
                session_id=session.id,
                action_type=_ACTION_FINISH_INITIATED,
                payload_summary=f"finish initiated for session {session.id}",
            )
        )

        # Attempt to create and persist the archive before marking finished.
        # If this fails, we do NOT change the session status (rollback semantics).
        archive = SessionArchive.from_session(session)
        try:
            await self._repo.insert_archive(archive)
        except Exception as exc:
            logger.error(
                "Archive creation failed for session_id=%s: %s",
                session.id,
                exc,
                exc_info=True,
            )
            await self._repo.insert_audit_event(
                AuditEvent.new(
                    session_id=session.id,
                    action_type=_ACTION_FINISH_FAILED,
                    payload_summary=f"archive creation failed: {exc}",
                )
            )
            raise ArchiveError(
                f"Failed to create archive for session {session.id!r}. "
                "The session has not been marked finished."
            ) from exc

        # Archive persisted — now mark the session as finished.
        session.status = SessionStatus.FINISHED
        session.updated_at = datetime.datetime.utcnow()
        await self._repo.upsert_session(session)

        await self._repo.insert_audit_event(
            AuditEvent.new(
                session_id=session.id,
                action_type=_ACTION_FINISHED,
                payload_summary=f"session {session.id} finished; archive {archive.id} created",
            )
        )

        # Clear in-memory reference — finished sessions must not be mutated.
        self._current = None

        await self._broadcast_session_update("session_finished")
        logger.info(
            "Session finished: session_id=%s archive_id=%s", session.id, archive.id
        )
        return archive

    # ------------------------------------------------------------------
    # State loading (used by recovery scanner)
    # ------------------------------------------------------------------

    def restore_session(self, session: Session) -> None:
        """
        Set the in-memory session directly (used by restart recovery).
        Must only be called during application startup before serving requests.
        """
        self._current = session
        logger.info(
            "Session restored from persistence: session_id=%s status=%s",
            session.id,
            session.status,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_mutable_session(self, operation: str) -> Session:
        """
        Return the current session if it exists and is not FINISHED.
        Raises InvalidTransitionError otherwise.
        """
        if self._current is None:
            raise InvalidTransitionError(
                f"Cannot {operation}: no active session exists."
            )
        if self._current.status == SessionStatus.FINISHED:
            raise InvalidTransitionError(
                f"Cannot {operation}: session {self._current.id!r} is FINISHED and immutable."
            )
        return self._current

    async def _broadcast_session_update(self, event: str) -> None:
        """Broadcast a session state change to all connected frontend clients."""
        try:
            payload: dict = {
                "event": event,
                "data": self._session_summary_dict(),
            }
            await self._manager.broadcast_to_frontends(
                {
                    "version": "1",
                    "type": "state_update",
                    "payload": payload,
                }
            )
        except Exception:
            logger.error("Failed to broadcast session update event=%s", event, exc_info=True)

    def _session_summary_dict(self) -> dict:
        """Build the session summary dict for broadcast and REST responses."""
        if self._current is None:
            return {"session": None}
        s = self._current
        return {
            "session_id": s.id,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
            "current_round_id": s.current_round_id,
            "active_game": s.active_game,
            "player_list": s.players,
            "standings": s.standings,
        }

    def get_summary(self) -> dict:
        """Return the current session summary dict for the REST API."""
        return self._session_summary_dict()
