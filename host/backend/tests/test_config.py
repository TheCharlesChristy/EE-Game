import pytest
from pydantic import ValidationError


def _fresh_settings(monkeypatch, overrides: dict):
    """Helper: clear the singleton, apply env overrides, return a new Settings instance."""
    import ee_game_backend.config as cfg_module

    cfg_module._settings = None
    for key, val in overrides.items():
        monkeypatch.setenv(key, val)
    from ee_game_backend.config import Settings

    return Settings()


def test_default_values_load(monkeypatch):
    """Default values are applied when no environment variables are set."""
    for var in ("BACKEND_HOST", "BACKEND_PORT", "LOG_LEVEL", "HEARTBEAT_TIMEOUT_SECONDS", "STATIC_FILES_DIR"):
        monkeypatch.delenv(var, raising=False)
    import ee_game_backend.config as cfg_module

    cfg_module._settings = None
    from ee_game_backend.config import Settings

    s = Settings()
    assert s.backend_host == "0.0.0.0"
    assert s.backend_port == 8000
    assert s.log_level == "INFO"
    assert s.heartbeat_timeout_seconds == 30
    assert s.static_files_dir == "../../frontend/dist"


def test_log_level_debug_accepted(monkeypatch):
    """LOG_LEVEL=DEBUG is a valid value."""
    s = _fresh_settings(monkeypatch, {"LOG_LEVEL": "DEBUG"})
    assert s.log_level == "DEBUG"


def test_invalid_log_level_raises(monkeypatch):
    """LOG_LEVEL=VERBOSE is not a recognised level and must raise a validation error."""
    import ee_game_backend.config as cfg_module

    cfg_module._settings = None
    monkeypatch.setenv("LOG_LEVEL", "VERBOSE")
    from ee_game_backend.config import Settings

    with pytest.raises((ValueError, ValidationError)):
        Settings()


def test_heartbeat_timeout_below_minimum_raises(monkeypatch):
    """HEARTBEAT_TIMEOUT_SECONDS=4 is below the minimum of 5 and must raise."""
    import ee_game_backend.config as cfg_module

    cfg_module._settings = None
    monkeypatch.setenv("HEARTBEAT_TIMEOUT_SECONDS", "4")
    from ee_game_backend.config import Settings

    with pytest.raises((ValueError, ValidationError)):
        Settings()


def test_backend_port_below_1024_raises(monkeypatch):
    """BACKEND_PORT=80 is a privileged port and must raise."""
    import ee_game_backend.config as cfg_module

    cfg_module._settings = None
    monkeypatch.setenv("BACKEND_PORT", "80")
    from ee_game_backend.config import Settings

    with pytest.raises((ValueError, ValidationError)):
        Settings()


def test_backend_port_above_65535_raises(monkeypatch):
    """BACKEND_PORT=99999 exceeds the maximum valid port number and must raise."""
    import ee_game_backend.config as cfg_module

    cfg_module._settings = None
    monkeypatch.setenv("BACKEND_PORT", "99999")
    from ee_game_backend.config import Settings

    with pytest.raises((ValueError, ValidationError)):
        Settings()


def test_get_settings_singleton(monkeypatch):
    """get_settings() returns the same object on repeated calls."""
    import ee_game_backend.config as cfg_module

    cfg_module._settings = None
    from ee_game_backend.config import get_settings

    first = get_settings()
    second = get_settings()
    assert first is second
    cfg_module._settings = None
