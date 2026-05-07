"""Retention sweeper for anonymised session archives."""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from .repository import SessionRepository


@dataclass(frozen=True)
class RetentionResult:
    expired_count: int
    cutoff: datetime.datetime


class RetentionSweeper:
    """Marks archives outside the retention window as expired."""

    def __init__(self, repo: SessionRepository, retention_days: int = 90) -> None:
        if retention_days < 1:
            raise ValueError("retention_days must be at least 1")
        self._repo = repo
        self._retention_days = retention_days

    async def sweep(self, now: datetime.datetime | None = None) -> RetentionResult:
        current = now or datetime.datetime.now(datetime.UTC)
        cutoff = current - datetime.timedelta(days=self._retention_days)
        expired = await self._repo.expire_archives_before(cutoff)
        return RetentionResult(expired_count=expired, cutoff=cutoff)
