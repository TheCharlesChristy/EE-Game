"""Diagnostics endpoints for deployment and classroom support."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..config import get_settings

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


class DiagnosticsResponse(BaseModel):
    ok: bool
    generated_at: str
    schema_version: int
    connected_devices: int
    current_session: dict
    table_counts: dict[str, int]
    wifi_ssid: str | None
    backend_ap_host: str


@router.get("", response_model=DiagnosticsResponse)
async def get_diagnostics(request: Request) -> DiagnosticsResponse:
    repo = request.app.state.repo
    manager = request.app.state.connection_manager
    session_service = request.app.state.session_service
    settings = get_settings()
    return DiagnosticsResponse(
        ok=True,
        generated_at=datetime.datetime.now(datetime.UTC).isoformat(),
        schema_version=await repo.get_schema_version(),
        connected_devices=await manager.get_device_count(),
        current_session=session_service.get_summary(),
        table_counts=await repo.get_table_counts(),
        wifi_ssid=settings.wifi_ssid,
        backend_ap_host=settings.backend_ap_host,
    )
