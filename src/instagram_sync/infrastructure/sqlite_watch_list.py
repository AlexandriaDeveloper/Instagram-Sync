"""تنفيذ WatchListRepository باستخدام نفس ملف SQLite المحلي."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from instagram_sync.domain.models import WatchProfile


class SQLiteWatchListRepository:
    """تخزين الحسابات التي اختارها المستخدم صراحةً للمزامنة عند فتح التطبيق."""

    def __init__(self, path: Path) -> None:
        """تهيئة Schema مستقلة عن جدول Media."""
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        """إنشاء Connection قصيرة العمر."""
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        """إنشاء جدول Watch List إن لم يكن موجودًا."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS watch_profiles (
                    profile TEXT PRIMARY KEY,
                    added_at TEXT NOT NULL,
                    last_checked_at TEXT
                )
                """
            )

    def list_profiles(self) -> list[WatchProfile]:
        """إرجاع الحسابات المختارة بترتيب الاسم."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT profile, last_checked_at
                FROM watch_profiles
                ORDER BY profile COLLATE NOCASE
                """
            ).fetchall()

        return [
            WatchProfile(
                profile=str(row["profile"]),
                last_checked_at=row["last_checked_at"],
            )
            for row in rows
        ]

    def add_profile(self, profile: str) -> None:
        """إضافة الحساب مرة واحدة فقط."""
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO watch_profiles(profile, added_at)
                VALUES (?, ?)
                """,
                (profile.lower(), now),
            )

    def remove_profile(self, profile: str) -> None:
        """إزالة الحساب من المتابعة المستقبلية."""
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM watch_profiles WHERE profile=?",
                (profile.lower(),),
            )

    def mark_checked(self, profile: str) -> None:
        """تحديث وقت آخر Check ناجح للحساب."""
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE watch_profiles
                SET last_checked_at=?
                WHERE profile=?
                """,
                (now, profile.lower()),
            )
