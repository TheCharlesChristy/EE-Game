"""
Background heartbeat monitor task.

Periodically scans the device registry for stale connections and pushes
state_update events to all connected frontend clients.

SRS reference: NFR-006, FR-023, FR-024.
"""

import asyncio
import logging
from typing import Any

from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


async def heartbeat_monitor(
    manager: ConnectionManager,
    timeout_seconds: int,
    registry: Any = None,
) -> None:
    """
    Background task that periodically checks for stale device connections.

    Runs indefinitely until cancelled (e.g. on app shutdown).
    Check interval is timeout_seconds / 2 to allow timely detection.
    SRS reference: NFR-006, FR-023, FR-024.
    """
    check_interval = max(timeout_seconds // 2, 5)
    while True:
        await asyncio.sleep(check_interval)
        try:
            stale_ids = await manager.mark_devices_stale(timeout_seconds)
            if stale_ids:
                logger.warning("Stale devices detected: %s", stale_ids)
                await manager.broadcast_to_frontends(
                    {
                        "version": "1",
                        "type": "state_update",
                        "payload": {
                            "event": "devices_stale",
                            "data": {"device_ids": stale_ids},
                        },
                    }
                )
                if registry is not None:
                    await registry.handle_stale(stale_ids)
        except Exception:
            logger.exception("Heartbeat monitor encountered an error; continuing")
