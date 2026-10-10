"""العقود Ports التي تفصل منطق التطبيق عن التقنيات الخارجية."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Protocol

from instagram_sync.domain.models import (
    MediaIdentity,
    RemoteMedia,
    SessionInfo,
    SyncRequest,
    SyncResult,
    WatchProfile,
)


class MediaSource(Protocol):
    """مصدر يستطيع إرجاع Media لحساب Instagram."""

    def iter_profile_media(
        self,
        profile_name: str,
        include_posts: bool = True,
        include_reels: bool = True,
    ) -> Iterable[RemoteMedia]: ...


class MediaCatalog(Protocol):
    """مخزن Metadata يعرف ما الذي تم تنزيله سابقًا."""

    def contains(self, profile: str, identity: MediaIdentity) -> bool: ...

    def record_media(
        self,
        profile: str,
        media: RemoteMedia,
        filename: str,
    ) -> None: ...

    def start_run(self, profile: str) -> int: ...

    def finish_run(
        self,
        run_id: int,
        downloaded: int,
        skipped: int,
        status: str,
        error: str | None = None,
    ) -> None: ...


class BinaryDownloader(Protocol):
    """مسؤول عن تنزيل ملف Binary من URL إلى Path."""

    def download(self, url: str, path: Path) -> None: ...


class BrowserSessionImporter(Protocol):
    """مسؤول عن استيراد Session من متصفح محلي."""

    def import_session(self, browser: str) -> SessionInfo: ...


class WatchListRepository(Protocol):
    """مخزن مستقل للحسابات التي اختار المستخدم متابعتها داخل البرنامج."""

    def list_profiles(self) -> list[WatchProfile]: ...

    def add_profile(self, profile: str) -> None: ...

    def remove_profile(self, profile: str) -> None: ...

    def mark_checked(self, profile: str) -> None: ...


class ProfileSyncExecutor(Protocol):
    """عقد يسمح بمزامنة حساب واحد بدون ربط Watch List بتنفيذ محدد."""

    def execute(
        self,
        request: SyncRequest,
        on_status: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> SyncResult: ...
