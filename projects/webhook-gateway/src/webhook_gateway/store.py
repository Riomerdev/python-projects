from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class EventStore:
    def __init__(self, database_path: str) -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS events (
                    source TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    PRIMARY KEY (source, event_id)
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def accept(self, source: str, event_id: str, payload: dict[str, Any]) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO events(source, event_id, received_at, payload, status)
                   VALUES (?, ?, ?, ?, 'accepted')""",
                (source, event_id, datetime.now(UTC).isoformat(), json.dumps(payload, sort_keys=True)),
            )
            return cursor.rowcount == 1

    def list_events(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT source, event_id, received_at, status FROM events ORDER BY received_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_event(self, source: str, event_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT source, event_id, received_at, payload, status FROM events WHERE source=? AND event_id=?",
                (source, event_id),
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["payload"] = json.loads(result["payload"])
        return result
