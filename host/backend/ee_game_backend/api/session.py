"""
Session lifecycle REST API for EP-02.
SRS reference: FR-001–FR-010, Section 8.1, Section 14.3, AC-009, AC-010.
"""

import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from ..session.exceptions import (
    ActiveSessionExistsError,
    ArchiveError,
    InvalidTransitionError,
    SessionNotFoundError,
)
from ..session.service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _get_service(request: Request) -> SessionService:
    """Extract SessionService from app.state."""
    return request.app.state.session_service


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class SessionSummaryResponse(BaseModel):
    """Current session state returned from GET /api/sessions/current."""

    session_id: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    current_round_id: str | None = None
    active_game: str | None = None
    player_list: list = []
    standings: list = []


class SessionCreatedResponse(BaseModel):
    session_id: str
    status: str
    created_at: str


class FinishConfirmationRequest(BaseModel):
    """
    Explicit confirmation is required before finishing a session.
    The host UI must set confirmed=True; the API rejects the request otherwise.
    SRS: EP-02-US-02 AC-1.
    """

    confirmed: bool = False


class FinishResponse(BaseModel):
    archive_id: str
    session_id: str
    finished_at: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SessionCreatedResponse)
async def create_session(request: Request):
    """
    Create a new ACTIVE session.
    Returns 409 if a non-finished session already exists (FR-010).
    """
    service = _get_service(request)
    try:
        session = await service.create_session()
    except ActiveSessionExistsError as exc:
        logger.warning("create_session rejected: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    return SessionCreatedResponse(
        session_id=session.id,
        status=session.status,
        created_at=session.created_at.isoformat(),
    )


@router.post("/resume", status_code=status.HTTP_200_OK, response_model=SessionCreatedResponse)
async def resume_session(request: Request):
    """
    Resume the latest non-FINISHED session.
    Returns 409 if an ACTIVE session already exists.
    Returns 404 if no resumable session exists.
    SRS: FR-002, FR-009.
    """
    service = _get_service(request)
    try:
        session = await service.resume_session()
    except ActiveSessionExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return SessionCreatedResponse(
        session_id=session.id,
        status=session.status,
        created_at=session.created_at.isoformat(),
    )


@router.get("/current", response_model=SessionSummaryResponse)
async def get_current_session(request: Request):
    """
    Return the current session state summary.
    Returns a response with all None fields if no session is active.
    SRS: FR-008.
    """
    service = _get_service(request)
    summary = service.get_summary()
    if summary.get("session") is None and "session_id" not in summary:
        return SessionSummaryResponse()
    return SessionSummaryResponse(
        session_id=summary.get("session_id"),
        status=summary.get("status"),
        created_at=summary.get("created_at"),
        updated_at=summary.get("updated_at"),
        current_round_id=summary.get("current_round_id"),
        active_game=summary.get("active_game"),
        player_list=summary.get("player_list", []),
        standings=summary.get("standings", []),
    )


@router.post(
    "/current/save", status_code=status.HTTP_200_OK, response_model=SessionCreatedResponse
)
async def save_session(request: Request):
    """
    Save the current session state to SQLite without ending the session.
    Returns 409 if no session exists or session is FINISHED.
    SRS: FR-003.
    """
    service = _get_service(request)
    try:
        session = await service.save_session()
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return SessionCreatedResponse(
        session_id=session.id,
        status=session.status,
        created_at=session.created_at.isoformat(),
    )


@router.post(
    "/current/pause", status_code=status.HTTP_200_OK, response_model=SessionCreatedResponse
)
async def pause_session(request: Request):
    """
    Pause the current ACTIVE session.
    Returns 409 if session is not ACTIVE or does not exist.
    SRS: FR-004.
    """
    service = _get_service(request)
    try:
        session = await service.pause_session()
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return SessionCreatedResponse(
        session_id=session.id,
        status=session.status,
        created_at=session.created_at.isoformat(),
    )


@router.post(
    "/current/finish", status_code=status.HTTP_200_OK, response_model=FinishResponse
)
async def finish_session(request: Request, body: FinishConfirmationRequest):
    """
    Permanently finish the current session.
    Requires {"confirmed": true} in the request body — returns 400 otherwise.
    Creates an anonymised archive and marks the session immutable.
    SRS: FR-005, FR-006, FR-007, EP-02-US-02 AC-1.
    """
    if not body.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Finish requires explicit confirmation. Send {"confirmed": true}.',
        )

    service = _get_service(request)
    try:
        archive = await service.finish_session()
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ArchiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    return FinishResponse(
        archive_id=archive.id,
        session_id=archive.session_id,
        finished_at=archive.finished_at.isoformat(),
        message="Session finished and archived successfully.",
    )
