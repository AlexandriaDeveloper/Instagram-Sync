from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class MediaKey:
    shortcode: str
    item_index: int


class MediaDatabase:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

    def _init_schema(self) -> None:
        with self._connect() as con:
            con.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile TEXT NOT NULL,
                    shortcode TEXT NOT NULL,
                    item_index INTEGER NOT NULL,
                    media_type TEXT NOT NULL,
                    post_date TEXT,
                    filename TEXT NOT NULL,
                    downloaded_at TEXT NOT NULL,
                    UNIQUE(profile, shortcode, item_index)
                );
                CREATE INDEX IF NOT EXISTS idx_media_profile
                    ON media(profile);
                CREATE TABLE IF NOT EXISTS sync_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    downloaded_count INTEGER NOT NULL DEFAULT 0,
                    skipped_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    error TEXT
                );
                """
            )

    def contains(self, profile: str, key: MediaKey) -> bool:
        with self._connect() as con:
            row = con.execute(
                "SELECT 1 FROM media WHERE profile=? AND shortcode=? AND item_index=?",
                (profile.lower(), key.shortcode, key.item_index),
            ).fetchone()
        return row is not None

    def record_media(
        self,
        profile: str,
        key: MediaKey,
        media_type: str,
        post_date: str | None,
        filename: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            con.execute(
                """
                INSERT OR IGNORE INTO media
                    (profile, shortcode, item_index, media_type, post_date, filename, downloaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.lower(),
                    key.shortcode,
                    key.item_index,
                    media_type,
                    post_date,
                    filename,
                    now,
                ),
            )

    def start_run(self, profile: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO sync_runs(profile, started_at, status) VALUES (?, ?, 'running')",
                (profile.lower(), now),
            )
            return int(cur.lastrowid)

    def finish_run(
        self,
        run_id: int,
        downloaded: int,
        skipped: int,
        status: str,
        error: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            con.execute(
                """
                UPDATE sync_runs
                SET finished_at=?, downloaded_count=?, skipped_count=?, status=?, error=?
                WHERE id=?
                """,
                (now, downloaded, skipped, status, error, run_id),
            )

    def profile_count(self, profile: str) -> int:
        with self._connect() as con:
            row = con.execute(
                "SELECT COUNT(*) AS c FROM media WHERE profile=?",
                (profile.lower(),),
            ).fetchone()
        return int(row["c"])
