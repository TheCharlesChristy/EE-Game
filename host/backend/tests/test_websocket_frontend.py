"""
Integration tests for the /ws/frontend WebSocket endpoint.

The frontend endpoint is receive-only from the client's perspective; the
backend sends an immediate device_list snapshot and then pushes state_update
events whenever authoritative state changes.
"""

import json

import pytest
from fastapi.testclient import TestClient

from ee_game_backend.core.constants import MSG_DEVICE_LIST, PROTOCOL_VERSION


@pytest.fixture
def ws_client(settings_override, monkeypatch):
    """Yield a TestClient with a fully started application lifespan."""
    for key, val in settings_override.items():
        monkeypatch.setenv(key, val)
    import ee_game_backend.config as cfg_module

    cfg_module._settings = None
    from ee_game_backend.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
    cfg_module._settings = None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_frontend_can_connect(ws_client):
    with ws_client.websocket_connect("/ws/frontend"):
        pass


def test_frontend_receives_device_list_on_connect(ws_client):
    """
    Immediately after connecting, the frontend must receive a device_list message
    containing the current snapshot (empty at startup).
    """
    with ws_client.websocket_connect("/ws/frontend") as ws:
        data = ws.receive_json()

    assert data["version"] == PROTOCOL_VERSION
    assert data["type"] == MSG_DEVICE_LIST
    assert "devices" in data["payload"]
    assert isinstance(data["payload"]["devices"], list)


def test_frontend_device_list_reflects_connected_device(ws_client):
    """
    A device that connects before the frontend should appear in the device_list.
    """
    # First connect a device so it appears in the registry.
    with ws_client.websocket_connect("/ws/devices/device-frontend-test") as device_ws:
        device_ws.send_text(
            json.dumps(
                {
                    "version": PROTOCOL_VERSION,
                    "type": "register",
                    "device_id": "device-frontend-test",
                    "payload": {
                        "firmware_version": "v1.0",
                        "board_target": "esp32c3",
                    },
                }
            )
        )

        # Now connect the frontend while the device is still connected.
        with ws_client.websocket_connect("/ws/frontend") as frontend_ws:
            data = frontend_ws.receive_json()

    assert data["type"] == MSG_DEVICE_LIST
    device_ids = [d["device_id"] for d in data["payload"]["devices"]]
    assert "device-frontend-test" in device_ids


def test_frontend_connection_closes_cleanly(ws_client):
    """Exiting the context manager closes the frontend WS without server error."""
    with ws_client.websocket_connect("/ws/frontend") as ws:
        # Consume the initial device_list.
        ws.receive_json()
    # Reaching here means no server-side crash occurred.
