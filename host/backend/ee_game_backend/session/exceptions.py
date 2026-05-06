"""
Session lifecycle exceptions for EP-02.
SRS reference: FR-001–FR-010.
"""


class SessionError(Exception):
    """Base exception for all session lifecycle errors."""


class InvalidTransitionError(SessionError):
    """
    Raised when a lifecycle command is issued from an invalid state.
    E.g. pausing a FINISHED session, finishing a session that does not exist.
    """


class ActiveSessionExistsError(SessionError):
    """
    Raised when the host attempts to create or resume a session while
    a non-finished session already exists.
    SRS reference: FR-010 — only one active gameplay session per host instance.
    """


class SessionNotFoundError(SessionError):
    """
    Raised when resume is requested but no resumable (non-FINISHED) session exists.
    SRS reference: FR-002.
    """


class ArchiveError(SessionError):
    """
    Raised when archive creation fails during finish.
    The finish operation must not silently succeed if the archive was not created.
    SRS reference: FR-007, EP-02-US-02 exception flow 1.
    """
