import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch  # noqa: F401 — available for test use


@pytest.fixture
def settings_override():
    """Return a dict of settings overrides suitable for use in monkeypatching."""
    return {
        "BACKEND_HOST": "127.0.0.1",
        "BACKEND_PORT": "8765",
        "LOG_LEVEL": "DEBUG",
        "HEARTBEAT_TIMEOUT_SECONDS": "10",
    }


@pytest.fixture
def client(settings_override, monkeypatch):
    for key, val in settings_override.items():
        monkeypatch.setenv(key, val)
    # Reset the cached settings singleton so the overrides take effect
    import ee_game_backend.config as cfg_module

    cfg_module._settings = None
    from ee_game_backend.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
    cfg_module._settings = None
