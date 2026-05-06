"""
Startup recovery scanner for EP-02.
Scans persisted sessions on application start and restores the latest consistent
non-FINISHED session into the SessionService.
SRS reference: FR-009, Section 13.3, NFR-007–NFR-010, AC-009.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from .models import Session, SessionStatus
from .repository import SessionRepository
from .service import SessionService

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    """
    Summary of the startup recovery scan.
    Exposed to operator-facing diagnostics (US-03 AC-4).
    """

    recovered: bool
    session_id: Optional[str]
    session_status: Optional[str]
    message: str


async def run_recovery(repo: SessionRepository, service: SessionService) -> RecoveryResult:
    """
    Scan persisted sessions and restore the latest consistent non-FINISHED session.

    Recovery rules (SRS Section 13.3):
    1. Look for the latest non-FINISHED session with a valid checksum.
    2. If found, restore it into the service via service.restore_session().
       - If its status is ACTIVE, keep it ACTIVE (it was running when the process died).
       - If its status is PAUSED, keep it PAUSED (it was explicitly paused before shutdown).
    3. If no resumable session is found, start with no active session (clean state).
    4. Finished archives are never loaded as active sessions.
    5. Corrupt rows are skipped and logged (NFR-008, NFR-009).

    The repository's get_latest_resumable_session() already handles corruption skipping
    and returns only ACTIVE/PAUSED sessions with valid checksums.

    Returns a RecoveryResult with the outcome details.
    """
    logger.info("Running startup recovery scan")

    candidate: Optional[Session] = None
    try:
        candidate = await repo.get_latest_resumable_session()
    except Exception:
        logger.error(
            "Recovery scan failed unexpectedly — starting with no active session",
            exc_info=True,
        )
        return RecoveryResult(
            recovered=False,
            session_id=None,
            session_status=None,
            message="Recovery scan error; starting with no active session. Check logs.",
        )

    if candidate is None:
        logger.info("Recovery scan: no resumable session found — starting clean")
        return RecoveryResult(
            recovered=False,
            session_id=None,
            session_status=None,
            message="No resumable session found. Ready to create a new session.",
        )

    # Valid candidate found — restore into the service.
    service.restore_session(candidate)

    result = RecoveryResult(
        recovered=True,
        session_id=candidate.id,
        session_status=candidate.status,
        message=(
            f"Recovered session {candidate.id!r} with status={candidate.status!r}. "
            "Use POST /api/sessions/resume to make it active."
            if candidate.status == SessionStatus.PAUSED
            else f"Recovered ACTIVE session {candidate.id!r}."
        ),
    )

    logger.info(
        "Recovery complete: session_id=%s status=%s",
        candidate.id,
        candidate.status,
    )
    return result
