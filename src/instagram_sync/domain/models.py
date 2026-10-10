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
    """نتيجة المزامنة التي تعرض للواجهة."""

    downloaded: int = 0
    skipped: int = 0


@dataclass(frozen=True, slots=True)
class SessionInfo:
    """معلومات Session ناجحة بدون أي Password أو Cookie values."""

    username: str
    browser: str
