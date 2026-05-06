"""
Registry domain exceptions for EP-03 (Player and Device Registry).
SRS reference: FR-011–FR-030, Section 8.3.
"""

import logging

logger = logging.getLogger(__name__)


class RegistryError(Exception):
    """Base exception for all player/device registry errors."""


class NoActiveSessionError(RegistryError):
    """Raised when a registry operation requires an active session but none exists."""


class CapacityError(RegistryError):
    """Raised when the session has reached its maximum device capacity (20 devices)."""


class RegistrationConflictError(RegistryError):
    """Raised when a device_id conflict is detected (potential impostor device)."""


class PlayerNotFoundError(RegistryError):
    """Raised when a player_id cannot be found in the current session."""


class ValidationError(RegistryError):
    """Raised when a username or colour value fails validation rules."""
