"""
MessageRouter: validates and dispatches incoming WebSocket messages from ESP32 devices.

SRS reference: IF-001 through IF-006.
"""

import datetime
import json
import logging
from typing import Any

from .connection_manager import ConnectionManager
from .constants import (
    CONN_CONNECTED,
    MSG_ERROR,
    MSG_EVENT,
    MSG_HEARTBEAT,
    MSG_REGISTER,
    MSG_STATE_UPDATE,
    MSG_TEST_EVENT,
    PROTOCOL_VERSION,
)
from ..games.validator import SchemaValidationError, validate_message

logger = logging.getLogger(__name__)


class MessageRouter:
    """
    Parses, validates, and dispatches incoming device messages.

    All public methods are guaranteed not to raise — every exception is caught,
    logged, and converted to an error response dict so that a single bad message
    cannot destabilise the host runtime.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def route_device_message(
        self,
        raw: str,
        device_id: str,
        manager: ConnectionManager,
        registry: Any = None,
        round_service: Any = None,
    ) -> dict | None:
        """
        Parse and dispatch a raw text message received from a device.

        Returns None on success (caller sends nothing back), or a dict that the
        caller should serialise and send to the device as an error response.
        Never raises.
        """
        try:
            return await self._dispatch(raw, device_id, manager, registry, round_service)
        except Exception:
            logger.error(
                "Unhandled exception in route_device_message for device_id=%s",
                device_id,
                exc_info=True,
            )
            return self._make_error(
                "INTERNAL_ERROR",
                "An internal error occurred while processing the message.",
            )

    # ------------------------------------------------------------------
    # Internal dispatch
    # ------------------------------------------------------------------

    async def _dispatch(
        self,
        raw: str,
        device_id: str,
        manager: ConnectionManager,
        registry: Any = None,
        round_service: Any = None,
    ) -> dict | None:
        # 1. Parse JSON
        try:
            envelope = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Invalid JSON from device_id=%s: %s | raw=%r",
                device_id,
                exc,
                raw,
            )
            return self._make_error("PARSE_ERROR", "Message is not valid JSON.")

        if not isinstance(envelope, dict):
            logger.warning(
                "Non-object JSON from device_id=%s: %r", device_id, raw
            )
            return self._make_error("PARSE_ERROR", "Message must be a JSON object.")

        # 2. Validate required envelope fields
        missing = [f for f in ("version", "type", "device_id") if f not in envelope]
        if missing:
            logger.warning(
                "Missing envelope fields %s from device_id=%s | raw=%r",
                missing,
                device_id,
                raw,
            )
            return self._make_error(
                "VALIDATION_FAILED",
                f"Missing required fields: {missing}.",
            )

        # 3. Check protocol version
        if envelope["version"] != PROTOCOL_VERSION:
            logger.warning(
                "Protocol version mismatch from device_id=%s: got %r, expected %r",
                device_id,
                envelope["version"],
                PROTOCOL_VERSION,
            )
            return self._make_error(
                "VALIDATION_FAILED",
                f"Unsupported protocol version {envelope['version']!r}; "
                f"expected {PROTOCOL_VERSION!r}.",
            )

        # 4. Verify device_id matches connection identity
        if envelope["device_id"] != device_id:
            logger.warning(
                "device_id mismatch: connection registered as %r but message claims %r",
                device_id,
                envelope["device_id"],
            )
            return self._make_error(
                "VALIDATION_FAILED",
                "device_id in message does not match connection identity.",
            )

        # 5. Dispatch on type
        msg_type = envelope.get("type")

        if msg_type == MSG_REGISTER:
            return await self._handle_register(envelope, device_id, manager, registry)
        if msg_type == MSG_HEARTBEAT:
            return await self._handle_heartbeat(envelope, device_id, manager, registry)
        if msg_type == MSG_TEST_EVENT:
            return await self._handle_test_event(envelope, device_id, registry, round_service)
        if msg_type == MSG_EVENT:
            return await self._handle_event(envelope, device_id, registry, round_service)

        logger.warning(
            "Unknown message type %r from device_id=%s", msg_type, device_id
        )
        return self._make_error(
            "UNKNOWN_TYPE",
            f"Received message type {msg_type!r} is not recognised by this server.",
        )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    async def _handle_register(
        self,
        envelope: dict,
        device_id: str,
        manager: ConnectionManager,
        registry: Any = None,
    ) -> None:
        try:
            validate_message(MSG_REGISTER, envelope)
        except SchemaValidationError as exc:
            return self._make_error("VALIDATION_FAILED", str(exc))

        payload = envelope.get("payload", {})
        firmware_version = payload.get("firmware_version", "unknown")
        board_target = payload.get("board_target", "unknown")

        await manager.update_device_info(
            device_id,
            firmware_version=firmware_version,
            board_target=board_target,
            connection_state=CONN_CONNECTED,
            last_seen_at=datetime.datetime.utcnow(),
        )

        await manager.broadcast_to_frontends(
            {
                "version": PROTOCOL_VERSION,
                "type": MSG_STATE_UPDATE,
                "payload": {
                    "event": "device_registered",
                    "data": {
                        "device_id": device_id,
                        "firmware_version": firmware_version,
                        "board_target": board_target,
                    },
                },
            }
        )

        if registry is not None:
            try:
                await registry.register_device(
                    device_id=device_id,
                    firmware_version=firmware_version,
                    board_target=board_target,
                )
            except Exception:
                logger.error(
                    "Registry registration failed for device_id=%s", device_id, exc_info=True
                )

        logger.info("Device registered: device_id=%s firmware=%s", device_id, firmware_version)
        return None

    async def _handle_heartbeat(
        self,
        envelope: dict,
        device_id: str,
        manager: ConnectionManager,
        registry: Any = None,
    ) -> None:
        try:
            validate_message(MSG_HEARTBEAT, envelope)
        except SchemaValidationError as exc:
            return self._make_error("VALIDATION_FAILED", str(exc))

        await manager.update_device_info(
            device_id,
            last_seen_at=datetime.datetime.utcnow(),
            connection_state=CONN_CONNECTED,
        )

        if registry is not None:
            try:
                await registry.handle_heartbeat(device_id)
            except Exception:
                logger.error(
                    "Registry heartbeat update failed for device_id=%s", device_id, exc_info=True
                )

        logger.debug("Heartbeat received from device_id=%s", device_id)
        return None

    async def _handle_test_event(
        self,
        envelope: dict,
        device_id: str,
        registry: Any = None,
        round_service: Any = None,
    ) -> dict | None:
        try:
            validate_message("event", envelope)
        except SchemaValidationError as exc:
            return self._make_error("VALIDATION_FAILED", str(exc))
        if round_service is None:
            return self._make_error("NO_ACTIVE_ROUND", "No round service is available.")
        player = None
        if registry is not None:
            player = await registry.get_player_by_device_id(device_id)
        result = await round_service.handle_test_event(
            device_id=device_id,
            payload=envelope.get("payload", {}),
            player=player.to_dict() if player is not None else None,
        )
        if result.get("accepted") is False:
            return self._make_error(result.get("code", "TEST_EVENT_REJECTED"), result["message"])
        return None

    async def _handle_event(
        self,
        envelope: dict,
        device_id: str,
        registry: Any = None,
        round_service: Any = None,
    ) -> dict | None:
        try:
            validate_message("event", envelope)
        except SchemaValidationError as exc:
            return self._make_error("VALIDATION_FAILED", str(exc))
        if round_service is None:
            return self._make_error("NO_ACTIVE_ROUND", "No round service is available.")
        player = None
        if registry is not None:
            player = await registry.get_player_by_device_id(device_id)
        result = await round_service.handle_device_event(
            device_id=device_id,
            payload=envelope.get("payload", {}),
            player=player.to_dict() if player is not None else None,
        )
        if result.get("accepted") is False:
            return self._make_error(result.get("code", "EVENT_REJECTED"), result["message"])
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_error(code: str, message: str) -> dict:
        return {
            "version": PROTOCOL_VERSION,
            "type": MSG_ERROR,
            "payload": {"code": code, "message": message},
        }
