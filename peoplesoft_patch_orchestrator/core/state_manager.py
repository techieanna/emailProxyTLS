from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import AgentResult, ExecutionEvent


class StateManager:
    """SQLite-backed state and checkpoint manager."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS execution_lock (
                    lock_key TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    acquired_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    environment TEXT,
                    agent TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS agent_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    environment TEXT,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    details TEXT NOT NULL,
                    errors TEXT NOT NULL
                );
                """
            )

    def acquire_lock(self, execution_id: str) -> bool:
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO execution_lock(lock_key, execution_id, acquired_at) VALUES (?, ?, datetime('now'))",
                    ("global_patch_lock", execution_id),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def release_lock(self, execution_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM execution_lock WHERE lock_key=? AND execution_id=?",
                ("global_patch_lock", execution_id),
            )

    def record_event(self, execution_id: str, event: ExecutionEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events(execution_id, event_type, environment, agent, payload, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_id,
                    event.event_type,
                    event.environment,
                    event.agent,
                    json.dumps(event.payload),
                    event.timestamp,
                ),
            )

    def record_result(self, execution_id: str, result: AgentResult) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_results(execution_id, agent, environment, status, started_at, completed_at, details, errors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_id,
                    result.agent,
                    result.environment,
                    result.status.value,
                    result.started_at,
                    result.completed_at,
                    json.dumps(result.details),
                    json.dumps(result.errors),
                ),
            )

    def get_completed_nodes(self, execution_id: str) -> set[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT agent, environment, status FROM agent_results WHERE execution_id=? AND status='SUCCESS'",
                (execution_id,),
            ).fetchall()
        return {f"{row['agent']}::{row['environment'] or 'global'}" for row in rows}

    def export_audit_trail(self, execution_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT event_type, environment, agent, payload, timestamp FROM events WHERE execution_id=? ORDER BY id",
                (execution_id,),
            ).fetchall()
        return [dict(row) for row in rows]
