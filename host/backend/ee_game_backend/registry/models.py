"""
Player domain model for EP-03 (Player and Device Registry).
SRS reference: FR-011–FR-030, Section 8.3, Section 9.3.
"""

import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Player:
    """
    Authoritative in-memory representation of a registered device/player.

    Stored as a dict inside Session.players and round-tripped via to_dict/from_dict.
    """

    player_id: str
    device_id: str
    username: str
    colour: str
    connection_state: str
    last_seen_at: datetime.datetime
    registered_at: datetime.datetime
    firmware_version: str
    board_target: str

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict for storage in Session.players."""
        return {
            "player_id": self.player_id,
            "device_id": self.device_id,
            "username": self.username,
            "colour": self.colour,
            "connection_state": self.connection_state,
            "last_seen_at": self.last_seen_at.isoformat(),
            "registered_at": self.registered_at.isoformat(),
            "firmware_version": self.firmware_version,
            "board_target": self.board_target,
        }

    @staticmethod
    def from_dict(data: dict) -> "Player":
        """
        Deserialise from stored dict. Robust to missing optional keys.

        Falls back to safe defaults for optional fields so that sessions
        persisted before an optional field was added can still be loaded.
        """
        return Player(
            player_id=data["player_id"],
            device_id=data["device_id"],
            username=data.get("username", "Unknown"),
            colour=data.get("colour", "#808080"),
            connection_state=data.get("connection_state", "disconnected"),
            last_seen_at=datetime.datetime.fromisoformat(
                data.get("last_seen_at", datetime.datetime.now(datetime.UTC).isoformat())
            ),
            registered_at=datetime.datetime.fromisoformat(
                data.get("registered_at", datetime.datetime.now(datetime.UTC).isoformat())
            ),
            firmware_version=data.get("firmware_version", "unknown"),
            board_target=data.get("board_target", "unknown"),
        )
