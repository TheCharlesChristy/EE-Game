"""
ConnectionManager: registry of active WebSocket connections for both ESP32 devices
and browser frontend clients.

SRS reference: IF-001 through IF-006, NFR-001 through NFR-010.
"""

import asyncio
import datetime
import logging
from dataclasses import dataclass, field

from fastapi import WebSocket

from .constants import CONN_STALE

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    device_id: str
    firmware_version: str
    board_target: str
    connection_state: str
    last_seen_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.UTC))


class ConnectionManager:
    """
    Thread-safe (asyncio.Lock) registry for device and frontend WebSocket connections.

    Single asyncio event loop — no thread-per-device pattern.
    All mutations go through the lock to serialise concurrent access from
    run_in_executor callbacks.
    """

    def __init__(self) -> None:
        self._lock: asyncio.Lock = asyncio.Lock()
        self._device_connections: dict[str, WebSocket] = {}
        self._frontend_connections: set[WebSocket] = set()
        self._device_info: dict[str, DeviceInfo] = {}

    # ------------------------------------------------------------------
    # Device connection management
    # ------------------------------------------------------------------

    async def connect_device(self, device_id: str, ws: WebSocket) -> None:
        """Register a device WebSocket connection and initialise its DeviceInfo."""
        async with self._lock:
            self._device_connections[device_id] = ws
            # Initialise with placeholder values — updated on receipt of register msg.
            if device_id not in self._device_info:
                self._device_info[device_id] = DeviceInfo(
                    device_id=device_id,
                    firmware_version="unknown",
                    board_target="unknown",
                    connection_state="connected",
                )
            else:
                self._device_info[device_id].connection_state = "connected"
                self._device_info[device_id].last_seen_at = datetime.datetime.now(datetime.UTC)

    async def disconnect_device(self, device_id: str) -> None:
        """Remove a device from the registry."""
        async with self._lock:
            self._device_connections.pop(device_id, None)
            if device_id in self._device_info:
                self._device_info[device_id].connection_state = "disconnected"

    # ------------------------------------------------------------------
    # Frontend connection management
    # ------------------------------------------------------------------

    async def connect_frontend(self, ws: WebSocket) -> None:
        """Register a frontend WebSocket connection."""
        async with self._lock:
            self._frontend_connections.add(ws)

    async def disconnect_frontend(self, ws: WebSocket) -> None:
        """Remove a frontend WebSocket connection."""
        async with self._lock:
            self._frontend_connections.discard(ws)

    # ------------------------------------------------------------------
    # Broadcast
    # ------------------------------------------------------------------

    async def broadcast_to_frontends(self, message: dict) -> None:
        """
        Send a JSON message to all connected frontend clients.

        Clients that raise during send are silently removed from the registry
        and logged at WARNING level — one bad client must not block others.
        """
        async with self._lock:
            snapshot = set(self._frontend_connections)

        failed: set[WebSocket] = set()
        for ws in snapshot:
            try:
                await ws.send_json(message)
            except Exception:
                logger.warning(
                    "Failed to send to frontend client; removing from registry",
                    exc_info=True,
                )
                failed.add(ws)

        if failed:
            async with self._lock:
                self._frontend_connections -= failed

    async def broadcast_to_devices(self, message: dict) -> None:
        """Send a JSON message to all currently connected devices."""
        async with self._lock:
            snapshot = dict(self._device_connections)

        failed: set[str] = set()
        for device_id, ws in snapshot.items():
            try:
                await ws.send_json(message)
            except Exception:
                logger.warning(
                    "Failed to send to device_id=%s; removing connection",
                    device_id,
                    exc_info=True,
                )
                failed.add(device_id)

        if failed:
            async with self._lock:
                for device_id in failed:
                    self._device_connections.pop(device_id, None)
                    if device_id in self._device_info:
                        self._device_info[device_id].connection_state = "disconnected"

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_connected_device_ids(self) -> list[str]:
        """Return a snapshot list of currently connected device IDs."""
        async with self._lock:
            return list(self._device_connections.keys())

    async def get_device_count(self) -> int:
        """Return the current number of connected devices."""
        async with self._lock:
            return len(self._device_connections)

    # ------------------------------------------------------------------
    # DeviceInfo management
    # ------------------------------------------------------------------

    async def update_device_info(self, device_id: str, **kwargs) -> None:
        """Update fields on an existing DeviceInfo entry for the given device."""
        async with self._lock:
            if device_id not in self._device_info:
                logger.warning(
                    "update_device_info called for unknown device_id=%s", device_id
                )
                return
            info = self._device_info[device_id]
            for key, value in kwargs.items():
                if hasattr(info, key):
                    setattr(info, key, value)
                else:
                    logger.warning(
                        "update_device_info: unknown field %r for DeviceInfo", key
                    )

    async def get_all_device_info(self) -> list[DeviceInfo]:
        """Return a snapshot list of all DeviceInfo records."""
        async with self._lock:
            return list(self._device_info.values())

    async def mark_devices_stale(self, timeout_seconds: int) -> list[str]:
        """
        Identify devices whose last_seen_at is older than timeout_seconds.

        Updates their connection_state to CONN_STALE and returns the list of
        stale device IDs.  Only considers currently connected devices.
        SRS reference: NFR-006, FR-023, FR-024.
        """
        now = datetime.datetime.now(datetime.UTC)
        cutoff = datetime.timedelta(seconds=timeout_seconds)
        stale_ids: list[str] = []

        async with self._lock:
            for device_id, info in self._device_info.items():
                # Only flag devices that are still in the active connections dict.
                if device_id not in self._device_connections:
                    continue
                age = now - info.last_seen_at
                if age > cutoff:
                    info.connection_state = CONN_STALE
                    stale_ids.append(device_id)

        return stale_ids
