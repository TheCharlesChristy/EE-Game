"""
Tests for MessageRouter.

SRS reference: IF-001 through IF-006.
"""

import json
from unittest.mock import AsyncMock, MagicMock


from ee_game_backend.core.message_router import MessageRouter
from ee_game_backend.core.constants import MSG_ERROR, PROTOCOL_VERSION


def _make_mock_manager():
    """Return an AsyncMock that satisfies the ConnectionManager interface."""
    manager = MagicMock()
    manager.update_device_info = AsyncMock()
    manager.broadcast_to_frontends = AsyncMock()
    return manager


def _valid_register(device_id: str = "d1") -> str:
    return json.dumps(
        {
            "version": PROTOCOL_VERSION,
            "type": "register",
            "device_id": device_id,
            "payload": {"firmware_version": "v1.0", "board_target": "esp32c3"},
        }
    )


def _valid_heartbeat(device_id: str = "d1") -> str:
    return json.dumps(
        {
            "version": PROTOCOL_VERSION,
            "type": "heartbeat",
            "device_id": device_id,
            "payload": {"timestamp_ms": 12345},
        }
    )


# ---------------------------------------------------------------------------
# Happy-path routing
# ---------------------------------------------------------------------------


async def test_valid_register_returns_none():
    router = MessageRouter()
    manager = _make_mock_manager()
    result = await router.route_device_message(_valid_register(), "d1", manager)
    assert result is None


async def test_valid_register_calls_update_device_info():
    router = MessageRouter()
    manager = _make_mock_manager()
    await router.route_device_message(_valid_register(), "d1", manager)
    manager.update_device_info.assert_awaited_once()
    call_kwargs = manager.update_device_info.call_args
    assert call_kwargs.args[0] == "d1"


async def test_valid_register_broadcasts_to_frontends():
    router = MessageRouter()
    manager = _make_mock_manager()
    await router.route_device_message(_valid_register(), "d1", manager)
    manager.broadcast_to_frontends.assert_awaited_once()
    broadcast_arg = manager.broadcast_to_frontends.call_args.args[0]
    assert broadcast_arg["payload"]["event"] == "device_registered"


async def test_valid_heartbeat_returns_none():
    router = MessageRouter()
    manager = _make_mock_manager()
    result = await router.route_device_message(_valid_heartbeat(), "d1", manager)
    assert result is None


async def test_valid_heartbeat_calls_update_device_info():
    router = MessageRouter()
    manager = _make_mock_manager()
    await router.route_device_message(_valid_heartbeat(), "d1", manager)
    manager.update_device_info.assert_awaited_once()


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


async def test_invalid_json_returns_parse_error():
    router = MessageRouter()
    manager = _make_mock_manager()
    result = await router.route_device_message("not json {{", "d1", manager)
    assert result is not None
    assert result["type"] == MSG_ERROR
    assert result["payload"]["code"] == "PARSE_ERROR"


async def test_missing_version_field_returns_error():
    router = MessageRouter()
    manager = _make_mock_manager()
    msg = json.dumps({"type": "register", "device_id": "d1", "payload": {}})
    result = await router.route_device_message(msg, "d1", manager)
    assert result is not None
    assert result["type"] == MSG_ERROR
    assert result["payload"]["code"] == "VALIDATION_FAILED"


async def test_missing_type_field_returns_error():
    router = MessageRouter()
    manager = _make_mock_manager()
    msg = json.dumps({"version": "1", "device_id": "d1", "payload": {}})
    result = await router.route_device_message(msg, "d1", manager)
    assert result is not None
    assert result["type"] == MSG_ERROR


async def test_missing_device_id_field_returns_error():
    router = MessageRouter()
    manager = _make_mock_manager()
    msg = json.dumps({"version": "1", "type": "register", "payload": {}})
    result = await router.route_device_message(msg, "d1", manager)
    assert result is not None
    assert result["type"] == MSG_ERROR
    assert result["payload"]["code"] == "VALIDATION_FAILED"


async def test_wrong_protocol_version_returns_error():
    router = MessageRouter()
    manager = _make_mock_manager()
    msg = json.dumps(
        {
            "version": "99",
            "type": "register",
            "device_id": "d1",
            "payload": {},
        }
    )
    result = await router.route_device_message(msg, "d1", manager)
    assert result is not None
    assert result["type"] == MSG_ERROR
    assert result["payload"]["code"] == "VALIDATION_FAILED"


async def test_unknown_message_type_returns_unknown_type_error():
    router = MessageRouter()
    manager = _make_mock_manager()
    msg = json.dumps(
        {
            "version": PROTOCOL_VERSION,
            "type": "launch_missiles",
            "device_id": "d1",
            "payload": {},
        }
    )
    result = await router.route_device_message(msg, "d1", manager)
    assert result is not None
    assert result["type"] == MSG_ERROR
    assert result["payload"]["code"] == "UNKNOWN_TYPE"


async def test_mismatched_device_id_returns_error():
    router = MessageRouter()
    manager = _make_mock_manager()
    # Message claims to be from "d2" but connection is identified as "d1"
    msg = json.dumps(
        {
            "version": PROTOCOL_VERSION,
            "type": "register",
            "device_id": "d2",
            "payload": {"firmware_version": "v1", "board_target": "esp32c3"},
        }
    )
    result = await router.route_device_message(msg, "d1", manager)
    assert result is not None
    assert result["type"] == MSG_ERROR
    assert result["payload"]["code"] == "VALIDATION_FAILED"


# ---------------------------------------------------------------------------
# Exception containment
# ---------------------------------------------------------------------------


async def test_exception_in_handler_is_converted_to_error_response():
    """An unexpected exception must not propagate out of route_device_message."""
    router = MessageRouter()
    manager = _make_mock_manager()
    # Make update_device_info raise to simulate an internal fault.
    manager.update_device_info = AsyncMock(side_effect=RuntimeError("db exploded"))

    result = await router.route_device_message(_valid_register(), "d1", manager)
    assert result is not None
    assert result["type"] == MSG_ERROR


# ---------------------------------------------------------------------------
# Error response shape
# ---------------------------------------------------------------------------


async def test_error_response_contains_version():
    router = MessageRouter()
    manager = _make_mock_manager()
    result = await router.route_device_message("bad json", "d1", manager)
    assert result["version"] == PROTOCOL_VERSION
