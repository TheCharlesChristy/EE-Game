from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    log_level: str = "INFO"
    heartbeat_timeout_seconds: int = 30
    static_files_dir: str = "../../frontend/dist"
    db_path: str = "data/sessions.db"

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
