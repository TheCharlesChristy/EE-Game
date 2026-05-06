"""
WebSocket endpoint for ESP32 device connections.

Devices connect to /ws/devices/{device_id}, send register + heartbeat messages,
and receive error responses when their messages are malformed.

SRS reference: IF-001, IF-002, IF-003, IF-004.
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...core.constants import MSG_STATE_UPDATE, PROTOCOL_VERSION

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/devices/{device_id}")
async def device_endpoint(ws: WebSocket, device_id: str) -> None:
    """
    Accept an ESP32 device connection, register it, and process its messages.

    Connection manager and message router are retrieved from app.state so that a
    single shared instance is used for the lifetime of the application — no
    dependency injection required for WebSocket endpoints.
    """
    manager = ws.app.state.connection_manager
    message_router = ws.app.state.message_router

    await ws.accept()
    await manager.connect_device(device_id, ws)
    logger.info("Device connected: device_id=%s", device_id)

    try:
        while True:
            raw = await ws.receive_text()
            registry = ws.app.state.registry
            round_service = getattr(ws.app.state, "round_service", None)
            response = await message_router.route_device_message(
                raw,
                device_id,
                manager,
                registry,
                round_service,
            )
            if response is not None:
                await ws.send_json(response)
    except WebSocketDisconnect:
        logger.info("Device disconnected: device_id=%s", device_id)
    except Exception:
        logger.error(
            "Unexpected error on device connection device_id=%s; closing",
            device_id,
            exc_info=True,
        )
    finally:
        await manager.disconnect_device(device_id)
        await manager.broadcast_to_frontends(
            {
                "version": PROTOCOL_VERSION,
                "type": MSG_STATE_UPDATE,
                "payload": {
                    "event": "device_disconnected",
                    "data": {"device_id": device_id},
                },
            }
        )
        registry = ws.app.state.registry
        if registry is not None:
            try:
                await registry.handle_disconnect(device_id)
            except Exception:
                logger.error(
                    "Registry disconnect handler failed for device_id=%s", device_id, exc_info=True
                )
