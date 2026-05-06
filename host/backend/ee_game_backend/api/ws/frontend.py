"""
WebSocket endpoint for browser frontend subscriptions.

Frontend clients connect to /ws/frontend to receive pushed state updates from
the backend.  They do not send messages — any incoming text is logged and
silently ignored.

SRS reference: IF-005, IF-006.
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...core.constants import MSG_DEVICE_LIST, PROTOCOL_VERSION

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/frontend")
async def frontend_endpoint(ws: WebSocket) -> None:
    """
    Accept a browser client connection and push state updates.

    The backend is the sole authority; frontends only receive pushed messages.
    """
    manager = ws.app.state.connection_manager

    await ws.accept()
    await manager.connect_frontend(ws)
    logger.info("Frontend client connected: client=%s", ws.client)

    # Send an immediate device list snapshot so the client can render without
    # waiting for an incremental event.
    device_info_list = await manager.get_all_device_info()
    await ws.send_json(
        {
            "version": PROTOCOL_VERSION,
            "type": MSG_DEVICE_LIST,
            "payload": {
                "devices": [
                    {
                        "device_id": d.device_id,
                        "firmware_version": d.firmware_version,
                        "board_target": d.board_target,
                        "connection_state": d.connection_state,
                        "last_seen_at": d.last_seen_at.isoformat(),
                    }
                    for d in device_info_list
                ]
            },
        }
    )

    try:
        while True:
            # Frontend clients are receive-only.  We must still await incoming
            # data to detect disconnects; any text received is logged and ignored.
            text = await ws.receive_text()
            logger.debug(
                "Frontend client sent a message (ignored): client=%s msg=%r",
                ws.client,
                text,
            )
    except WebSocketDisconnect:
        logger.info("Frontend client disconnected: client=%s", ws.client)
    except Exception:
        logger.error(
            "Unexpected error on frontend connection client=%s; closing",
            ws.client,
            exc_info=True,
        )
    finally:
        await manager.disconnect_frontend(ws)
