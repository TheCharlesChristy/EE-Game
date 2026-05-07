from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Search for .env relative to this file, then fall back to the repo root.
# This works both on a deployed Pi (/opt/ee-game/host/backend/.env) and in
# a dev checkout where only the repo-root .env template exists.
_CONFIG_DIR = Path(__file__).resolve().parent.parent  # host/backend/
_ROOT_DIR = _CONFIG_DIR.parent.parent                  # repo root


def _locate_env() -> str | None:
    for candidate in [_CONFIG_DIR / ".env", _ROOT_DIR / ".env"]:
        if candidate.exists():
            return str(candidate)
    return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_locate_env(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    log_level: str = "INFO"
    heartbeat_timeout_seconds: int = 30
    static_files_dir: str = "../../frontend/dist"
    db_path: str = "data/sessions.db"

    # WiFi access-point settings (read-only at runtime — set via .env)
    wifi_ssid: str | None = None
    wifi_password: str | None = None  # never logged
    backend_ap_host: str = "192.168.4.1"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(
                f"log_level must be one of {sorted(allowed)}, got {v!r}"
            )
        return upper

    @field_validator("heartbeat_timeout_seconds")
    @classmethod
    def validate_heartbeat_timeout(cls, v: int) -> int:
        if v < 5:
            raise ValueError(
                f"heartbeat_timeout_seconds must be >= 5, got {v}"
            )
        return v

    @field_validator("backend_port")
    @classmethod
    def validate_backend_port(cls, v: int) -> int:
        if not (1024 <= v <= 65535):
            raise ValueError(
                f"backend_port must be between 1024 and 65535, got {v}"
            )
        return v


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
