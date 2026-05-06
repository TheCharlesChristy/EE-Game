import json
from unittest.mock import AsyncMock

from ee_game_backend.core.constants import PROTOCOL_VERSION
from ee_game_backend.core.message_router import MessageRouter


async def test_router_accepts_20_heartbeat_messages_without_error():
    router = MessageRouter()
    manager = AsyncMock()
    for idx in range(20):
        device_id = f"d{idx}"
        result = await router.route_device_message(
            json.dumps(
                {
                    "version": PROTOCOL_VERSION,
                    "type": "heartbeat",
                    "device_id": device_id,
                    "payload": {"timestamp_ms": idx},
                }
            ),
            device_id,
            manager,
        )
        assert result is None
