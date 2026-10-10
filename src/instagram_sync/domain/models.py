"""نماذج المجال الأساسية.

هذه الكائنات لا تعرف شيئًا عن Qt أو SQLite أو Instaloader.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MediaIdentity:
    """هوية عنصر Media بشكل ثابت تمنع تكرار التنزيل."""

    shortcode: str
    item_index: int


@dataclass(frozen=True, slots=True)
class RemoteMedia:
    """وصف عنصر Media قادم من المصدر قبل تنزيله."""

    identity: MediaIdentity
    url: str
    media_type: str
    post_date: str | None
    extension: str


@dataclass(frozen=True, slots=True)
class SyncRequest:
    """مدخلات عملية مزامنة واحدة."""

    profile: str
    destination: Path
    include_posts: bool = True
    include_reels: bool = True


@dataclass(slots=True)
class SyncResult:
    """نتيجة مزامنة حساب واحد."""

    downloaded: int = 0
    skipped: int = 0


@dataclass(frozen=True, slots=True)
class SessionInfo:
    """معلومات Session تم التحقق منها بدون Password."""

    username: str


@dataclass(frozen=True, slots=True)
class WatchProfile:
    """حساب اختاره المستخدم صراحةً للمزامنة عند فتح البرنامج."""

    profile: str
    last_checked_at: str | None = None


@dataclass(slots=True)
class WatchSyncSummary:
    """ملخص مزامنة كل الحسابات الموجودة في Watch List."""

    checked_profiles: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed_profiles: int = 0
