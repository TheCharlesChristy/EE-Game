"""
Tests for the heartbeat_monitor background task.

SRS reference: NFR-006, FR-023, FR-024.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


from ee_game_backend.core.heartbeat import heartbeat_monitor
from ee_game_backend.core.connection_manager import ConnectionManager


def _make_mock_manager(stale_ids: list[str] | None = None):
    manager = MagicMock()
    manager.mark_devices_stale = AsyncMock(return_value=stale_ids or [])
    manager.broadcast_to_frontends = AsyncMock()
    return manager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _run_one_cycle(manager, timeout_seconds: int = 10) -> None:
    """
    Run the heartbeat monitor for exactly one check cycle.

    We patch asyncio.sleep to a no-op so the test completes instantly,
    then cancel the task after the first real iteration body runs.
    """
    call_count = 0

    async def fake_sleep(_):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            # Allow the task to run one full iteration, then stop it.
            raise asyncio.CancelledError

    with patch("ee_game_backend.core.heartbeat.asyncio.sleep", side_effect=fake_sleep):
        try:
            await heartbeat_monitor(manager, timeout_seconds)
        except asyncio.CancelledError:
            pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_heartbeat_monitor_calls_mark_devices_stale():
    """Monitor must call mark_devices_stale at least once per cycle."""
    manager = _make_mock_manager(stale_ids=[])

    await _run_one_cycle(manager)

    manager.mark_devices_stale.assert_awaited()


async def test_heartbeat_monitor_broadcasts_when_stale_devices_found():
    """When stale devices are found, broadcast_to_frontends must be called."""
    manager = _make_mock_manager(stale_ids=["device-1", "device-2"])

    await _run_one_cycle(manager)

    manager.broadcast_to_frontends.assert_awaited_once()
    broadcast_arg = manager.broadcast_to_frontends.call_args.args[0]
    assert broadcast_arg["payload"]["event"] == "devices_stale"
    assert set(broadcast_arg["payload"]["data"]["device_ids"]) == {
        "device-1",
        "device-2",
    }


async def test_heartbeat_monitor_does_not_broadcast_when_no_stale_devices():
    """When no devices are stale, broadcast_to_frontends must NOT be called."""
    manager = _make_mock_manager(stale_ids=[])

    await _run_one_cycle(manager)

    manager.broadcast_to_frontends.assert_not_awaited()


async def test_heartbeat_monitor_continues_after_mark_devices_stale_raises():
    """
    If mark_devices_stale raises an exception the monitor must NOT propagate it;
    it logs and continues (fault tolerance).
    """
    call_count = 0
    manager = _make_mock_manager()

    async def flaky_mark(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("transient DB error")
        return []

    manager.mark_devices_stale = AsyncMock(side_effect=flaky_mark)

    # We need at least 2 cycles: one that raises and one that succeeds.
    iteration = 0

    async def fake_sleep(_):
        nonlocal iteration
        iteration += 1
        if iteration >= 3:
            raise asyncio.CancelledError

    with patch("ee_game_backend.core.heartbeat.asyncio.sleep", side_effect=fake_sleep):
        try:
            await heartbeat_monitor(manager, timeout_seconds=10)
        except asyncio.CancelledError:
            pass

    # mark_devices_stale should have been called twice (once raising, once succeeding)
    assert manager.mark_devices_stale.await_count >= 2


async def test_heartbeat_monitor_check_interval_respects_minimum():
    """
    Check interval must be max(timeout // 2, 5).
    With timeout=8, interval should be 4 clamped to 5.
    """
    sleep_calls: list[int] = []
    manager = _make_mock_manager()

    async def capture_sleep(interval):
        sleep_calls.append(interval)
        raise asyncio.CancelledError

    with patch("ee_game_backend.core.heartbeat.asyncio.sleep", side_effect=capture_sleep):
        try:
            await heartbeat_monitor(manager, timeout_seconds=8)
        except asyncio.CancelledError:
            pass

    assert sleep_calls[0] == 5  # max(8 // 2, 5) == max(4, 5) == 5


async def test_heartbeat_monitor_integration_with_real_manager():
    """
    Smoke test: run one cycle against a real ConnectionManager (no mocks).
    No devices connected → no stale IDs → broadcast not called.
    """
    manager = ConnectionManager()
    manager.broadcast_to_frontends = AsyncMock()

    async def fake_sleep(_):
        raise asyncio.CancelledError

    with patch("ee_game_backend.core.heartbeat.asyncio.sleep", side_effect=fake_sleep):
        try:
            await heartbeat_monitor(manager, timeout_seconds=30)
        except asyncio.CancelledError:
            pass

    manager.broadcast_to_frontends.assert_not_awaited()
