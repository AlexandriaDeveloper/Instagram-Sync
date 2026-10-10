"""تنفيذ MediaCatalog باستخدام SQLite المحلية."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from instagram_sync.domain.models import MediaIdentity, RemoteMedia


class SQLiteMediaCatalog:
    """تخزين Metadata للمزامنة بدون تخزين Password أو Cookies."""

    def __init__(self, path: Path) -> None:
        """تهيئة المسار ثم إنشاء Schema إن لم تكن موجودة."""
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        """إنشاء Connection قصيرة العمر لكل عملية."""
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        """إنشاء جداول Media وسجل عمليات Sync."""
        with self._connect() as connection:
            connection.executescript(
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

    def contains(self, profile: str, identity: MediaIdentity) -> bool:
        """معرفة هل العنصر تم تنزيله سابقًا."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM media
                WHERE profile=? AND shortcode=? AND item_index=?
                """,
                (profile.lower(), identity.shortcode, identity.item_index),
            ).fetchone()
        return row is not None

    def record_media(
        self,
        profile: str,
        media: RemoteMedia,
        filename: str,
    ) -> None:
        """تسجيل عنصر تم تنزيله بنجاح؛ UNIQUE يمنع التكرار."""
        now = datetime.now(UTC).isoformat()

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO media
                    (
                        profile, shortcode, item_index, media_type,
                        post_date, filename, downloaded_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.lower(),
                    media.identity.shortcode,
                    media.identity.item_index,
                    media.media_type,
                    media.post_date,
                    filename,
                    now,
                ),
            )

    def start_run(self, profile: str) -> int:
        """بدء سجل Audit لعملية Sync وإرجاع رقمها."""
        now = datetime.now(UTC).isoformat()

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO sync_runs(profile, started_at, status)
                VALUES (?, ?, 'running')
                """,
                (profile.lower(), now),
            )
            return int(cursor.lastrowid)

    def finish_run(
        self,
        run_id: int,
        downloaded: int,
        skipped: int,
        status: str,
        error: str | None = None,
    ) -> None:
        """إغلاق سجل Sync بالنتيجة النهائية."""
        now = datetime.now(UTC).isoformat()

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE sync_runs
                SET
                    finished_at=?,
                    downloaded_count=?,
                    skipped_count=?,
                    status=?,
                    error=?
                WHERE id=?
                """,
                (now, downloaded, skipped, status, error, run_id),
            )

    def profile_count(self, profile: str) -> int:
        """دالة مساعدة للاختبارات ومعرفة عدد العناصر المسجلة للحساب."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM media WHERE profile=?",
                (profile.lower(),),
            ).fetchone()
        return int(row["count"])
