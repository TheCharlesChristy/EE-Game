"""
Colour palette and allocator for EP-03 (Player and Device Registry).
SRS reference: FR-013, FR-015, FR-017, Section 8.3.
"""

import logging

from .exceptions import CapacityError

logger = logging.getLogger(__name__)

COLOUR_PALETTE: list[str] = [
    "#E6194B",
    "#3CB44B",
    "#4363D8",
    "#F58231",
    "#911EB4",
    "#42D4F4",
    "#F032E6",
    "#BFEF45",
    "#FABED4",
    "#469990",
    "#DCBEFF",
    "#9A6324",
    "#FFFAC8",
    "#800000",
    "#AAFFC3",
    "#808000",
    "#FFD8B1",
    "#000075",
    "#A9A9A9",
    "#808080",
]


def is_valid_colour(colour: str) -> bool:
    """
    Return True if colour is a member of COLOUR_PALETTE.

    Comparison is case-insensitive to be robust against capitalisation variations.
    """
    upper = colour.upper()
    return any(c.upper() == upper for c in COLOUR_PALETTE)


class ColourAllocator:
    """
    Session-scoped colour pool manager.

    Picks colours from COLOUR_PALETTE in order, skipping those already assigned.
    The allocate() method is stateless with respect to this object — it relies on
    the caller to pass the current list of assigned colours (exclude).  The release()
    method is provided for API completeness but is not required by the current design.
    """

    def __init__(self) -> None:
        # No per-instance state is strictly required for the current allocation
        # strategy, but the class is retained as a session-scoped object to allow
        # future stateful optimisations (e.g. priority queues, custom ordering).
        self._released: list[str] = []

    def allocate(self, exclude: list[str]) -> str:
        """
        Return the first colour from COLOUR_PALETTE not in the exclude list.

        Raises CapacityError if all 20 palette entries are already assigned.

        Args:
            exclude: List of colour strings already assigned to players in the session.

        Returns:
            A hex colour string from COLOUR_PALETTE.
        """
        exclude_upper = {c.upper() for c in exclude}
        for colour in COLOUR_PALETTE:
            if colour.upper() not in exclude_upper:
                return colour
        raise CapacityError(
            "All 20 colours in the palette are already assigned. "
            "The session has reached maximum capacity."
        )

    def release(self, colour: str) -> None:
        """
        Mark a colour as available again.

        Not required by the current design (exclusion lists are derived from live
        session state on every call) but provided for completeness and future use.
        """
        self._released.append(colour)
