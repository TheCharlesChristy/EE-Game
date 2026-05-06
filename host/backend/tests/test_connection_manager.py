"""
Tests for ConnectionManager.

SRS reference: IF-001 through IF-006.
"""

import datetime
from unittest.mock import AsyncMock, MagicMock


from ee_game_backend.core.connection_manager import ConnectionManager
from ee_game_backend.core.constants import CONN_STALE


def _make_mock_ws():
    """Return an AsyncMock that behaves like a FastAPI WebSocket."""
    ws = MagicMock()
    ws.send_json = AsyncMock()
    return ws


# ---------------------------------------------------------------------------
# connect_device / get_device_count
# ---------------------------------------------------------------------------


async def test_connect_device_adds_to_registry():
    manager = ConnectionManager()
    ws = _make_mock_ws()
    await manager.connect_device("device-1", ws)
    assert await manager.get_device_count() == 1


async def test_connect_device_initialises_device_info():
    manager = ConnectionManager()
    ws = _make_mock_ws()
    await manager.connect_device("device-1", ws)
    info_list = await manager.get_all_device_info()
    assert len(info_list) == 1
    assert info_list[0].device_id == "device-1"


async def test_get_connected_device_ids_returns_ids():
    manager = ConnectionManager()
    ws1, ws2 = _make_mock_ws(), _make_mock_ws()
    await manager.connect_device("d1", ws1)
    await manager.connect_device("d2", ws2)
    ids = await manager.get_connected_device_ids()
    assert set(ids) == {"d1", "d2"}


# ---------------------------------------------------------------------------
# disconnect_device
# ---------------------------------------------------------------------------


async def test_disconnect_device_removes_from_registry():
    manager = ConnectionManager()
    ws = _make_mock_ws()
    await manager.connect_device("device-1", ws)
    await manager.disconnect_device("device-1")
    assert await manager.get_device_count() == 0


async def test_disconnect_device_marks_info_disconnected():
    manager = ConnectionManager()
    ws = _make_mock_ws()
    await manager.connect_device("device-1", ws)
    await manager.disconnect_device("device-1")
    info_list = await manager.get_all_device_info()
    assert info_list[0].connection_state == "disconnected"


async def test_disconnect_unknown_device_does_not_raise():
    manager = ConnectionManager()
    # Should complete without raising even if device was never registered.
    await manager.disconnect_device("ghost-device")


# ---------------------------------------------------------------------------
# mark_devices_stale
# ---------------------------------------------------------------------------


async def test_mark_devices_stale_marks_old_devices():
    manager = ConnectionManager()
    ws = _make_mock_ws()
    await manager.connect_device("old-device", ws)
    # Backdate last_seen_at so the device appears stale.
    async with manager._lock:
        manager._device_info["old-device"].last_seen_at = (
            datetime.datetime.utcnow() - datetime.timedelta(seconds=100)
        )

    stale = await manager.mark_devices_stale(timeout_seconds=30)
    assert "old-device" in stale
    info_list = await manager.get_all_device_info()
    stale_info = next(i for i in info_list if i.device_id == "old-device")
    assert stale_info.connection_state == CONN_STALE


async def test_mark_devices_stale_ignores_recent_devices():
    manager = ConnectionManager()
    ws = _make_mock_ws()
    await manager.connect_device("fresh-device", ws)
    # last_seen_at defaults to utcnow() — should NOT be stale with 30 s timeout.

    stale = await manager.mark_devices_stale(timeout_seconds=30)
    assert "fresh-device" not in stale


async def test_mark_devices_stale_ignores_disconnected_devices():
    """Devices not in _device_connections should not be flagged stale."""
    manager = ConnectionManager()
    ws = _make_mock_ws()
    await manager.connect_device("device-1", ws)
    # Backdate and then disconnect.
    async with manager._lock:
        manager._device_info["device-1"].last_seen_at = (
            datetime.datetime.utcnow() - datetime.timedelta(seconds=200)
        )
    await manager.disconnect_device("device-1")

    stale = await manager.mark_devices_stale(timeout_seconds=30)
    assert "device-1" not in stale


# ---------------------------------------------------------------------------
# broadcast_to_frontends
# ---------------------------------------------------------------------------


async def test_broadcast_to_frontends_sends_to_all_clients():
    manager = ConnectionManager()
    ws1, ws2 = _make_mock_ws(), _make_mock_ws()
    await manager.connect_frontend(ws1)
    await manager.connect_frontend(ws2)

    msg = {"version": "1", "type": "state_update", "payload": {"event": "test"}}
    await manager.broadcast_to_frontends(msg)

    ws1.send_json.assert_awaited_once_with(msg)
    ws2.send_json.assert_awaited_once_with(msg)


async def test_broadcast_to_frontends_removes_faulty_client():
    """A client that raises during send should be removed; others still receive."""
    manager = ConnectionManager()
    good_ws = _make_mock_ws()
    bad_ws = _make_mock_ws()
    bad_ws.send_json = AsyncMock(side_effect=RuntimeError("connection closed"))

    await manager.connect_frontend(good_ws)
    await manager.connect_frontend(bad_ws)

    msg = {"version": "1", "type": "state_update", "payload": {}}
    await manager.broadcast_to_frontends(msg)

    # good client received the message
    good_ws.send_json.assert_awaited_once_with(msg)
    # faulty client has been removed
    async with manager._lock:
        assert bad_ws not in manager._frontend_connections


# ---------------------------------------------------------------------------
# update_device_info / get_all_device_info
# ---------------------------------------------------------------------------


async def test_update_device_info_updates_fields():
    manager = ConnectionManager()
    ws = _make_mock_ws()
    await manager.connect_device("d1", ws)
    await manager.update_device_info("d1", firmware_version="v2.0", board_target="esp32c3")

    info_list = await manager.get_all_device_info()
    info = info_list[0]
    assert info.firmware_version == "v2.0"
    assert info.board_target == "esp32c3"


async def test_update_device_info_unknown_device_logs_warning(caplog):
    manager = ConnectionManager()
    import logging

    with caplog.at_level(logging.WARNING):
        await manager.update_device_info("nonexistent", firmware_version="v1")
    assert "unknown device_id" in caplog.text


# ---------------------------------------------------------------------------
# Frontend connect / disconnect
# ---------------------------------------------------------------------------


async def test_connect_and_disconnect_frontend():
    manager = ConnectionManager()
    ws = _make_mock_ws()
    await manager.connect_frontend(ws)
    async with manager._lock:
        assert ws in manager._frontend_connections

    await manager.disconnect_frontend(ws)
    async with manager._lock:
        assert ws not in manager._frontend_connections
