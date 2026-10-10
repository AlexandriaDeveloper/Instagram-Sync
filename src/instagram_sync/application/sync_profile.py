"""Use Case الخاص بمزامنة حساب Instagram."""

from __future__ import annotations

from collections.abc import Callable

from instagram_sync.application.ports import BinaryDownloader, MediaCatalog, MediaSource
from instagram_sync.application.profile_name import normalize_profile_name
from instagram_sync.domain.models import RemoteMedia, SyncRequest, SyncResult


class SyncCancelled(Exception):
    """استثناء واضح عند طلب المستخدم إلغاء المزامنة."""


class SyncProfileUseCase:
    """تنسيق عملية المزامنة بدون معرفة تفاصيل Instagram أو SQLite أو HTTP."""

    def __init__(
        self,
        source: MediaSource,
        catalog: MediaCatalog,
        downloader: BinaryDownloader,
    ) -> None:
        """حقن Dependencies حتى يسهل الاستبدال والاختبار."""
        self._source = source
        self._catalog = catalog
        self._downloader = downloader

    def execute(
        self,
        request: SyncRequest,
        on_status: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> SyncResult:
        """تنفيذ Full/Incremental Sync حسب ما هو موجود في الـCatalog."""
        profile = normalize_profile_name(request.profile)

        # كل حساب يأخذ مجلد مستقل لمنع خلط ملفات الحسابات.
        profile_dir = request.destination / profile
        profile_dir.mkdir(parents=True, exist_ok=True)

        result = SyncResult()
        run_id = self._catalog.start_run(profile)

        def status(message: str) -> None:
            """تمرير رسائل التقدم للواجهة إن كانت موجودة."""
            if on_status:
                on_status(message)

        try:
            status(f"Reading @{profile}...")

            for media in self._source.iter_profile_media(
                profile,
                request.include_posts,
                request.include_reels,
            ):
                if should_cancel and should_cancel():
                    raise SyncCancelled("Synchronization cancelled.")

                # Source of Truth هي قاعدة البيانات، وليس مجرد وجود اسم الملف.
                if self._catalog.contains(profile, media.identity):
                    result.skipped += 1
                    continue

                filename = self._filename(media)
                path = profile_dir / filename

                status(f"Downloading {filename}")
                self._downloader.download(media.url, path)

                # لا نسجل العنصر إلا بعد اكتمال التنزيل بنجاح.
                self._catalog.record_media(profile, media, str(path))
                result.downloaded += 1

            self._catalog.finish_run(
                run_id,
                result.downloaded,
                result.skipped,
                "success",
            )
            status(
                f"Done. Downloaded {result.downloaded}, skipped {result.skipped}."
            )
            return result

        except Exception as exc:
            # هذا Boundary مقصود لتسجيل نتيجة Run حتى لو كان الخطأ من شبكة أو Instagram.
            self._catalog.finish_run(
                run_id,
                result.downloaded,
                result.skipped,
                "failed",
                str(exc),
            )
            raise

    @staticmethod
    def _filename(media: RemoteMedia) -> str:
        """إنشاء اسم ملف ثابت وقابل لإعادة البناء من هوية العنصر."""
        return (
            f"{media.identity.shortcode}_"
            f"{media.identity.item_index:02d}{media.extension}"
        )
