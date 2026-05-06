"""
Integration tests for the /ws/devices/{device_id} WebSocket endpoint.

Uses FastAPI TestClient with websocket_connect so the full stack
(endpoint → message_router → connection_manager) is exercised.
"""

import json

import pytest
from fastapi.testclient import TestClient

from ee_game_backend.core.constants import MSG_ERROR, PROTOCOL_VERSION


@pytest.fixture
def ws_client(settings_override, monkeypatch):
    """Yield a TestClient whose lifespan is fully started (manager on app.state)."""
    for key, val in settings_override.items():
        monkeypatch.setenv(key, val)
    import ee_game_backend.config as cfg_module

    cfg_module._settings = None
    from ee_game_backend.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
    cfg_module._settings = None


def _register_msg(device_id: str = "device-abc") -> str:
    return json.dumps(
        {
            "version": PROTOCOL_VERSION,
            "type": "register",
            "device_id": device_id,
            "payload": {"firmware_version": "v1.0", "board_target": "esp32c3"},
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_device_can_connect(ws_client):
    with ws_client.websocket_connect("/ws/devices/device-abc"):
        # Connection was accepted; no exception means success.
        pass


def test_device_valid_register_does_not_crash_server(ws_client):
    with ws_client.websocket_connect("/ws/devices/device-abc") as ws:
        ws.send_text(_register_msg("device-abc"))
        # No response expected for a valid register message; connection is still open.
        # Verify we can still send another message without the server crashing.
        ws.send_text(_register_msg("device-abc"))


def test_device_malformed_json_returns_error_response(ws_client):
    with ws_client.websocket_connect("/ws/devices/device-abc") as ws:
        ws.send_text("{this is not json")
        data = ws.receive_json()
    assert data["type"] == MSG_ERROR
    assert data["payload"]["code"] == "PARSE_ERROR"


def test_device_unknown_type_returns_error_without_disconnect(ws_client):
    with ws_client.websocket_connect("/ws/devices/device-abc") as ws:
        ws.send_text(
            json.dumps(
                {
                    "version": PROTOCOL_VERSION,
                    "type": "do_something_weird",
                    "device_id": "device-abc",
                    "payload": {},
                }
            )
        )
        data = ws.receive_json()
        # Connection is still alive — we can send another message.
        ws.send_text(_register_msg("device-abc"))
    assert data["type"] == MSG_ERROR
    assert data["payload"]["code"] == "UNKNOWN_TYPE"


def test_device_connection_closes_cleanly(ws_client):
    """Exiting the context manager closes the WS cleanly without server error."""
    with ws_client.websocket_connect("/ws/devices/device-xyz") as ws:
        ws.send_text(_register_msg("device-xyz"))
    # If we reach here the server did not crash.


def test_device_wrong_protocol_version_returns_error(ws_client):
    with ws_client.websocket_connect("/ws/devices/device-abc") as ws:
        ws.send_text(
            json.dumps(
                {
                    "version": "99",
                    "type": "register",
                    "device_id": "device-abc",
                    "payload": {},
                }
            )
        )
        data = ws.receive_json()
    assert data["type"] == MSG_ERROR
    assert data["payload"]["code"] == "VALIDATION_FAILED"
