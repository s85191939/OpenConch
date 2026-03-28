"""
Memory change history — SQLite-backed audit log.

Every add, update, delete is recorded with timestamps,
enabling full memory provenance and debugging.
"""

import sqlite3
import json
import os
from typing import List, Optional
from openconch.utils import now_timestamp, generate_id


class HistoryStore:
    """SQLite-backed memory change history."""

    def __init__(self, db_path: str = ".openconch/history.db"):
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create the history table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_history (
                    id TEXT PRIMARY KEY,
                    memory_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_content TEXT,
                    new_content TEXT,
                    metadata TEXT,
                    timestamp REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_id
                ON memory_history(memory_id)
            """)

    def record(
        self,
        memory_id: str,
        action: str,
        old_content: Optional[str] = None,
        new_content: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """Record a memory change event."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO memory_history (id, memory_id, action, old_content, new_content, metadata, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    generate_id(),
                    memory_id,
                    action,
                    old_content,
                    new_content,
                    json.dumps(metadata) if metadata else None,
                    now_timestamp(),
                ),
            )

    def get_history(self, memory_id: str) -> List[dict]:
        """Get all history entries for a specific memory."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM memory_history WHERE memory_id = ? ORDER BY timestamp DESC",
                (memory_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_recent(self, limit: int = 50) -> List[dict]:
        """Get most recent history entries across all memories."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM memory_history ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
