"""
PlayerRegistryService: authoritative player/device registry for EP-03.
SRS reference: FR-011–FR-030, Section 8.3.
"""

import datetime
import logging
import re
import uuid
from typing import Any

from ..core.constants import (
    CONN_CONNECTED,
    CONN_DISCONNECTED,
    CONN_STALE,
    PROTOCOL_VERSION,
)
from ..session.models import AuditEvent, SessionStatus
from .colour_palette import ColourAllocator, is_valid_colour
from .exceptions import (
    CapacityError,
    NoActiveSessionError,
    PlayerNotFoundError,
    ValidationError,
)
from .models import Player
from .username_generator import UsernameGenerator

logger = logging.getLogger(__name__)

# Validation constants.
_USERNAME_MAX_LEN = 20
_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_ -]+$")

# Audit action-type constants.
_ACTION_REGISTERED = "device_registered"
_ACTION_RECONNECTED = "device_reconnected"
_ACTION_DISCONNECTED = "device_disconnected"
_ACTION_STALE = "devices_stale"
_ACTION_USERNAME_CHANGED = "player_username_changed"
_ACTION_COLOUR_CHANGED = "player_colour_changed"


class PlayerRegistryService:
    """
    Authoritative player/device registry for an active session.

    Responsibilities:
    - Register new devices and assign generated username + colour.
    - Detect and restore existing player mappings on reconnect.
    - Detect and log identity conflicts (potential impostor devices).
    - Update device liveness state (connected/stale/disconnected).
    - Enable host edits of username and colour with validation.
    - Persist player state changes via SessionRepository.
    - Broadcast player list updates via ConnectionManager.
    - Emit structured audit events for all significant operations.

    SRS reference: FR-011 to FR-030, Section 8.3.
    """

    MAX_DEVICES = 20

    def __init__(
        self,
        session_service: Any,
        repo: Any,
        manager: Any,
    ) -> None:
        self._session_service = session_service
        self._repo = repo
        self._manager = manager
        self._username_generator = UsernameGenerator()
        self._colour_allocator = ColourAllocator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def register_device(
        self,
        device_id: str,
        firmware_version: str,
        board_target: str,
    ) -> Player:
        """
        Register a device into the active session.

        Flow:
        1. Require an active (non-FINISHED, non-None) session.
        2. Load current players from session.players.
        3. If device_id already exists:
           a. If connection_state is "connected": log WARNING (reconnect conflict).
           b. Restore mapping — update connection_state, last_seen_at, firmware, board.
           c. Persist and broadcast.
           d. Emit audit event: action_type="device_reconnected".
           e. Return restored Player.
        4. If device_id is new:
           a. Enforce capacity limit.
           b. Allocate colour and generate username.
           c. Create Player and append to session.players.
           d. Persist and broadcast.
           e. Emit audit event: action_type="device_registered".
           f. Return new Player.

        Raises: NoActiveSessionError, CapacityError.
        """
        session = self._get_active_session()
        players = self._load_players(session)

        existing = next((p for p in players if p.device_id == device_id), None)

        if existing is not None:
            if existing.connection_state == CONN_CONNECTED:
                logger.warning(
                    "RECONNECT_CONFLICT: device_id=%s reconnected while still marked connected "
                    "— old WebSocket connection was likely dropped without a clean disconnect",
                    device_id,
                )
            now = datetime.datetime.utcnow()
            existing.connection_state = CONN_CONNECTED
            existing.last_seen_at = now
            existing.firmware_version = firmware_version
            existing.board_target = board_target
            await self._save_players(session, players)
            await self._broadcast_player_list(players, "player_list_updated")
            await self._emit_audit(
                session.id,
                _ACTION_RECONNECTED,
                f"device_id={device_id} restored player_id={existing.player_id}",
            )
            logger.info(
                "Device reconnected: device_id=%s player_id=%s",
                device_id,
                existing.player_id,
            )
            return existing

        # New device — enforce capacity.
        if len(players) >= self.MAX_DEVICES:
            raise CapacityError(
                f"Session is at maximum capacity ({self.MAX_DEVICES} devices). "
                f"Cannot register device_id={device_id!r}."
            )

        existing_colours = [p.colour for p in players]
        existing_usernames = [p.username for p in players]

        colour = self._colour_allocator.allocate(exclude=existing_colours)
        username = self._username_generator.generate(exclude=existing_usernames)

        now = datetime.datetime.utcnow()
        player = Player(
            player_id=str(uuid.uuid4()),
            device_id=device_id,
            username=username,
            colour=colour,
            connection_state=CONN_CONNECTED,
            last_seen_at=now,
            registered_at=now,
            firmware_version=firmware_version,
            board_target=board_target,
        )
        players.append(player)
        await self._save_players(session, players)
        await self._emit_audit(
            session.id,
            _ACTION_REGISTERED,
            f"device_id={device_id} registered as player_id={player.player_id} "
            f"username={username!r} colour={colour}",
        )
        await self._broadcast_player_list(players, "player_list_updated")
        logger.info(
            "Device registered: device_id=%s player_id=%s username=%r colour=%s",
            device_id,
            player.player_id,
            username,
            colour,
        )
        return player

    async def handle_heartbeat(self, device_id: str) -> None:
        """
        Update last_seen_at and connection_state="connected" for device_id.

        No-op if device_id is not in session players or no active session.
        Never raises.
        SRS: FR-022, FR-023.
        """
        try:
            session = self._session_service.current_session
            if session is None or session.status == SessionStatus.FINISHED:
                return
            players = self._load_players(session)
            player = next((p for p in players if p.device_id == device_id), None)
            if player is None:
                return
            player.connection_state = CONN_CONNECTED
            player.last_seen_at = datetime.datetime.utcnow()
            await self._save_players(session, players)
        except Exception:
            logger.error(
                "handle_heartbeat failed for device_id=%s", device_id, exc_info=True
            )

    async def handle_disconnect(self, device_id: str) -> None:
        """
        Set connection_state="disconnected" for device_id, persist and broadcast.

        No-op if device_id is not in session players or no active session.
        Never raises.
        Emits audit event: action_type="device_disconnected".
        SRS: FR-024.
        """
        try:
            session = self._session_service.current_session
            if session is None or session.status == SessionStatus.FINISHED:
                return
            players = self._load_players(session)
            player = next((p for p in players if p.device_id == device_id), None)
            if player is None:
                return
            player.connection_state = CONN_DISCONNECTED
            player.last_seen_at = datetime.datetime.utcnow()
            await self._save_players(session, players)
            await self._broadcast_player_list(
                players,
                "player_list_updated",
                extra_data={"device_ids": [device_id]},
            )
            await self._emit_audit(
                session.id,
                _ACTION_DISCONNECTED,
                f"device_id={device_id} disconnected",
            )
            logger.info("Device disconnected: device_id=%s", device_id)
        except Exception:
            logger.error(
                "handle_disconnect failed for device_id=%s", device_id, exc_info=True
            )

    async def handle_stale(self, device_ids: list[str]) -> None:
        """
        Set connection_state="stale" for all device_ids present in session players.

        Persists and broadcasts stale alert for affected players.
        No-op if no active session.
        Never raises.
        Emits audit event: action_type="devices_stale".
        SRS: FR-024.
        """
        try:
            session = self._session_service.current_session
            if session is None or session.status == SessionStatus.FINISHED:
                return
            players = self._load_players(session)
            device_id_set = set(device_ids)
            affected: list[str] = []
            for player in players:
                if player.device_id in device_id_set:
                    player.connection_state = CONN_STALE
                    player.last_seen_at = datetime.datetime.utcnow()
                    affected.append(player.device_id)
            if not affected:
                return
            await self._save_players(session, players)
            await self._broadcast_player_list(
                players,
                "player_list_updated",
                extra_data={"device_ids": affected},
            )
            await self._emit_audit(
                session.id,
                _ACTION_STALE,
                f"devices_stale: {', '.join(affected)}",
            )
            logger.info("Devices marked stale: %s", affected)
        except Exception:
            logger.error("handle_stale failed for device_ids=%s", device_ids, exc_info=True)

    async def update_player_username(
        self, player_id: str, username: str
    ) -> Player:
        """
        Update the username for the given player_id.

        Validation:
        - 1–20 characters
        - Matches [A-Za-z0-9_ -]+
        - Not empty after stripping whitespace

        Raises: NoActiveSessionError, PlayerNotFoundError, ValidationError.
        SRS: FR-014, FR-017.
        """
        session = self._get_active_session()
        self._validate_username(username)
        players = self._load_players(session)
        player = next((p for p in players if p.player_id == player_id), None)
        if player is None:
            raise PlayerNotFoundError(
                f"No player with player_id={player_id!r} found in the current session."
            )
        old_username = player.username
        player.username = username
        await self._save_players(session, players)
        await self._broadcast_player_list(players, "player_list_updated")
        await self._emit_audit(
            session.id,
            _ACTION_USERNAME_CHANGED,
            f"player_id={player_id} username changed from {old_username!r} to {username!r}",
            actor_type="host",
        )
        logger.info(
            "Username updated: player_id=%s %r -> %r", player_id, old_username, username
        )
        return player

    async def update_player_colour(
        self, player_id: str, colour: str
    ) -> Player:
        """
        Update the colour for the given player_id.

        Validation:
        - colour must be in COLOUR_PALETTE
        - colour must not already be assigned to a different player

        Raises: NoActiveSessionError, PlayerNotFoundError, ValidationError.
        SRS: FR-015, FR-017.
        """
        session = self._get_active_session()
        if not is_valid_colour(colour):
            raise ValidationError(
                f"Colour {colour!r} is not a valid palette colour. "
                "Choose from the defined COLOUR_PALETTE."
            )
        players = self._load_players(session)
        player = next((p for p in players if p.player_id == player_id), None)
        if player is None:
            raise PlayerNotFoundError(
                f"No player with player_id={player_id!r} found in the current session."
            )
        # Check uniqueness — the target colour must not be held by a different player.
        colour_upper = colour.upper()
        conflict = next(
            (
                p
                for p in players
                if p.colour.upper() == colour_upper and p.player_id != player_id
            ),
            None,
        )
        if conflict is not None:
            raise ValidationError(
                f"Colour {colour!r} is already assigned to player_id={conflict.player_id!r}. "
                "Each player must have a unique colour."
            )
        old_colour = player.colour
        player.colour = colour.upper()
        await self._save_players(session, players)
        await self._broadcast_player_list(players, "player_list_updated")
        await self._emit_audit(
            session.id,
            _ACTION_COLOUR_CHANGED,
            f"player_id={player_id} colour changed from {old_colour} to {player.colour}",
            actor_type="host",
        )
        logger.info(
            "Colour updated: player_id=%s %s -> %s", player_id, old_colour, colour
        )
        return player

    async def get_all_players(self) -> list[Player]:
        """
        Return all Player objects from the current session.

        Returns empty list if no active session.
        Never raises.
        """
        try:
            session = self._session_service.current_session
            if session is None or session.status == SessionStatus.FINISHED:
                return []
            return self._load_players(session)
        except Exception:
            logger.error("get_all_players failed", exc_info=True)
            return []

    async def get_player_by_device_id(self, device_id: str) -> Player | None:
        """
        Return the Player for device_id, or None if not found or no active session.

        Never raises.
        """
        try:
            session = self._session_service.current_session
            if session is None or session.status == SessionStatus.FINISHED:
                return None
            players = self._load_players(session)
            return next((p for p in players if p.device_id == device_id), None)
        except Exception:
            logger.error(
                "get_player_by_device_id failed for device_id=%s", device_id, exc_info=True
            )
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_active_session(self) -> Any:
        """
        Return the current session if it is active (not None, not FINISHED).

        Raises NoActiveSessionError if no qualifying session exists.
        """
        session = self._session_service.current_session
        if session is None:
            raise NoActiveSessionError(
                "No active session exists. Create or resume a session first."
            )
        if session.status == SessionStatus.FINISHED:
            raise NoActiveSessionError(
                f"Session {session.id!r} is FINISHED and cannot accept new registrations."
            )
        return session

    def _load_players(self, session: Any) -> list[Player]:
        """Deserialise session.players (list of dicts) into Player objects."""
        players: list[Player] = []
        for raw in session.players:
            try:
                players.append(Player.from_dict(raw))
            except Exception:
                logger.error(
                    "Failed to deserialise player record from session_id=%s: %r",
                    session.id,
                    raw,
                    exc_info=True,
                )
        return players

    async def _save_players(self, session: Any, players: list[Player]) -> None:
        """
        Serialise Player objects back to dicts, update session.players, and persist.
        """
        session.players = [p.to_dict() for p in players]
        session.updated_at = datetime.datetime.utcnow()
        await self._repo.upsert_session(session)

    async def _broadcast_player_list(
        self,
        players: list[Player],
        event: str,
        extra_data: dict | None = None,
    ) -> None:
        """
        Broadcast a player_list_updated message to all frontend clients.

        Broadcast failures are logged but not re-raised (same pattern as
        SessionService._broadcast_session_update).
        """
        try:
            data: dict = {"players": [p.to_dict() for p in players]}
            if extra_data:
                data.update(extra_data)
            message = {
                "version": PROTOCOL_VERSION,
                "type": "state_update",
                "payload": {
                    "event": event,
                    "data": data,
                },
            }
            await self._manager.broadcast_to_frontends(message)
        except Exception:
            logger.error(
                "Failed to broadcast player list update event=%s", event, exc_info=True
            )

    async def _emit_audit(
        self,
        session_id: str,
        action_type: str,
        payload_summary: str,
        actor_type: str = "device",
    ) -> None:
        """Persist a structured audit event. Failures are logged but not re-raised."""
        event = AuditEvent.new(
            session_id=session_id,
            action_type=action_type,
            actor_type=actor_type,
            payload_summary=payload_summary,
        )
        await self._repo.insert_audit_event(event)

    @staticmethod
    def _validate_username(username: str) -> None:
        """
        Validate a username against the rules defined in US-03.

        Raises ValidationError for any rule violation.
        """
        if not username or not username.strip():
            raise ValidationError("Username must not be empty or consist only of whitespace.")
        if len(username) > _USERNAME_MAX_LEN:
            raise ValidationError(
                f"Username must be at most {_USERNAME_MAX_LEN} characters; "
                f"got {len(username)}."
            )
        if not _USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username may only contain letters, digits, underscores, spaces, and hyphens."
            )
