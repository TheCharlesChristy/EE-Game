import platform
import sys

from fastapi import APIRouter

from ..config import get_settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Lightweight liveness check. Returns 200 with runtime diagnostics."""
    settings = get_settings()
    return {
        "status": "ok",
        "python_version": sys.version,
        "platform": platform.platform(),
        "log_level": settings.log_level,
        "heartbeat_timeout_seconds": settings.heartbeat_timeout_seconds,
    }
