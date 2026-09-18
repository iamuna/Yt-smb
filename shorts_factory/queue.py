from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import DATA_DIR

DB_PATH = DATA_DIR / "queue.db"


@dataclass
class QueueItem:
    id: int
    video_path: str
    title: str
    description: str
    tags: list[str]
    privacy_status: str
    status: str
    created_at: str
    youtube_video_id: str | None = None


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS upload_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_path TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            privacy_status TEXT NOT NULL DEFAULT 'private',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            youtube_video_id TEXT
        )
        """
    )
    connection.commit()
    return connection


def enqueue(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str = "private",
) -> int:
    with _connect() as db:
        cursor = db.execute(
            """
            INSERT INTO upload_queue
            (video_path, title, description, tags_json, privacy_status, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                str(video_path.resolve()),
                title[:100],
                description,
                json.dumps(tags[:15], ensure_ascii=False),
                privacy_status,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        db.commit()
        return int(cursor.lastrowid)


def _row_to_item(row: sqlite3.Row) -> QueueItem:
    return QueueItem(
        id=int(row["id"]),
        video_path=str(row["video_path"]),
        title=str(row["title"]),
        description=str(row["description"]),
        tags=list(json.loads(row["tags_json"] or "[]")),
        privacy_status=str(row["privacy_status"]),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
        youtube_video_id=row["youtube_video_id"],
    )


def next_pending() -> QueueItem | None:
    with _connect() as db:
        row = db.execute(
            "SELECT * FROM upload_queue WHERE status='pending' ORDER BY id ASC LIMIT 1"
        ).fetchone()
        return _row_to_item(row) if row else None


def list_recent(limit: int = 20) -> list[QueueItem]:
    with _connect() as db:
        rows = db.execute(
            "SELECT * FROM upload_queue ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_row_to_item(row) for row in rows]


def mark_uploaded(item_id: int, youtube_video_id: str) -> None:
    with _connect() as db:
        db.execute(
            """
            UPDATE upload_queue
            SET status='uploaded', youtube_video_id=?
            WHERE id=?
            """,
            (youtube_video_id, item_id),
        )
        db.commit()


def mark_failed(item_id: int) -> None:
    with _connect() as db:
        db.execute(
            "UPDATE upload_queue SET status='failed' WHERE id=?",
            (item_id,),
        )
        db.commit()
