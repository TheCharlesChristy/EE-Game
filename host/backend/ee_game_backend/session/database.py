"""
SQLite connection setup and schema migration entry point.
SRS reference: Section 9.1, Section 9.2, Section 9.3, AC-012.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any

from .migrations import apply_migrations

logger = logging.getLogger(__name__)


class AsyncCursor:
    """Small awaitable/async-context cursor wrapper over sqlite3.Cursor."""

    def __init__(self, cursor: sqlite3.Cursor) -> None:
        self._cursor = cursor

    def __await__(self):
        async def _ready():
            return self

        return _ready().__await__()

    async def __aenter__(self) -> "AsyncCursor":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._cursor.close()

    async def fetchone(self) -> sqlite3.Row | None:
        return self._cursor.fetchone()

    async def fetchall(self) -> list[sqlite3.Row]:
        return self._cursor.fetchall()

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount


class AsyncSQLiteConnection:
    """
    Async-compatible wrapper for sqlite3.

    The repository API is async so callers never block on a persistence-specific
    interface. For this local-first Pi app, the actual sqlite3 calls are short
    and serialized by SQLite itself, avoiding aiosqlite worker-thread stalls seen
    under the current Python 3.13 sandbox.
    """

    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row

    @property
    def row_factory(self) -> Any:
        return self._conn.row_factory

    @row_factory.setter
    def row_factory(self, value: Any) -> None:
        self._conn.row_factory = value

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> AsyncCursor:
        return AsyncCursor(self._conn.execute(sql, parameters))

    async def executemany(self, sql: str, seq_of_parameters) -> AsyncCursor:
        return AsyncCursor(self._conn.executemany(sql, seq_of_parameters))

    async def executescript(self, sql: str) -> None:
        self._conn.executescript(sql)

    async def commit(self) -> None:
        self._conn.commit()

    async def close(self) -> None:
        self._conn.close()


async def open_database(db_path: str) -> AsyncSQLiteConnection:
    """
    Open (or create) the SQLite database, ensure the schema exists, and
    return the connection.  The caller is responsible for closing it.
    """
    path = Path(db_path)
    if db_path != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)

    db = AsyncSQLiteConnection(db_path)
    schema_version = await apply_migrations(db)
    logger.info(
        "SQLite database opened at %s (schema_version=%d)",
        path.resolve() if db_path != ":memory:" else ":memory:",
        schema_version,
    )
    return db
