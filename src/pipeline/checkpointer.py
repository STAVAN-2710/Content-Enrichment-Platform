"""
SQLite-backed checkpointer — tracks per-episode processing status.

Enables pipeline resumption: crashed or quota-exhausted runs skip already-
successful episodes on the next run. Every record carries which prompt and
schema versions produced it, so re-enrichment can be targeted when either changes.
"""
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class CheckpointRecord:
    episode_id: str
    status: str          # "success" | "failed"
    prompt_version: Optional[str]
    schema_version: Optional[int]
    processed_at: datetime
    error_type: Optional[str]
    error_msg: Optional[str]


class Checkpointer:
    """Thread-safe SQLite checkpointer for the enrichment pipeline."""

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episode_status (
                    episode_id     TEXT PRIMARY KEY,
                    status         TEXT NOT NULL,
                    prompt_version TEXT,
                    schema_version INTEGER,
                    processed_at   TEXT NOT NULL,
                    error_type     TEXT,
                    error_msg      TEXT
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_status ON episode_status(status)"
            )

    def is_processed(self, episode_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT status FROM episode_status WHERE episode_id = ? AND status = 'success'",
                (episode_id,),
            ).fetchone()
        return row is not None

    def mark_success(
        self,
        episode_id: str,
        prompt_version: str,
        schema_version: int,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO episode_status
                    (episode_id, status, prompt_version, schema_version, processed_at, error_type, error_msg)
                VALUES (?, 'success', ?, ?, ?, NULL, NULL)
                """,
                (episode_id, prompt_version, schema_version, _now()),
            )

    def mark_failed(
        self,
        episode_id: str,
        error_type: str,
        error_msg: str,
        prompt_version: Optional[str] = None,
        schema_version: Optional[int] = None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO episode_status
                    (episode_id, status, prompt_version, schema_version, processed_at, error_type, error_msg)
                VALUES (?, 'failed', ?, ?, ?, ?, ?)
                """,
                (episode_id, prompt_version, schema_version, _now(), error_type, error_msg[:1000]),
            )

    def stats(self) -> dict[str, int]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS n FROM episode_status GROUP BY status"
            ).fetchall()
        return {row["status"]: row["n"] for row in rows}

    def unprocessed_ids(self, all_ids: list[str]) -> list[str]:
        """Return episode IDs from all_ids that have NOT been successfully processed."""
        with self._conn() as conn:
            done = {
                row[0]
                for row in conn.execute(
                    "SELECT episode_id FROM episode_status WHERE status = 'success'"
                ).fetchall()
            }
        return [eid for eid in all_ids if eid not in done]


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
