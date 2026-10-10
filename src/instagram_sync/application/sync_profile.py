"""Use Case الخاص بمزامنة حساب Instagram."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import CancelledError

from instagram_sync.application.errors import InstagramRateLimitError
from instagram_sync.application.ports import BinaryDownloader, MediaCatalog, MediaSource
from instagram_sync.application.profile_name import normalize_profile_name
from instagram_sync.domain.models import RemoteMedia, SyncRequest, SyncResult


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
        on_progress: Callable[[int, int], None] | None = None,
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

        def progress(current: int, total: int) -> None:
            """تمرير تقدم دقيق؛ total=-1 يعني أن مرحلة الحصر ما زالت جارية."""
            if on_progress:
                on_progress(current, total)

        try:
            status(f"Scanning @{profile} to count media files...")
            progress(0, -1)

            media_items: list[RemoteMedia] = []
            for media in self._source.iter_profile_media(
                profile,
                request.include_posts,
                request.include_reels,
                should_cancel=should_cancel,
            ):
                if should_cancel and should_cancel():
                    raise CancelledError("Synchronization cancelled.")
                media_items.append(media)
                progress(len(media_items), -1)

            total = len(media_items)
            progress(0, total)
            status(f"Found {total} media file(s) for @{profile}.")

            for index, media in enumerate(media_items, start=1):
                if should_cancel and should_cancel():
                    raise CancelledError("Synchronization cancelled.")

                # Source of Truth هي قاعدة البيانات، وليس مجرد وجود اسم الملف.
                if self._catalog.contains(profile, media.identity):
                    result.skipped += 1
                    progress(index, total)
                    continue

                filename = self._filename(media)
                path = profile_dir / filename

                status(f"Downloading {filename}")
                self._downloader.download(media.url, path)

                # لا نسجل العنصر إلا بعد اكتمال التنزيل بنجاح.
                self._catalog.record_media(profile, media, str(path))
                result.downloaded += 1
                progress(index, total)

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

        except CancelledError as exc:
            self._catalog.finish_run(
                run_id,
                result.downloaded,
                result.skipped,
                "cancelled",
                str(exc),
            )
            status("Synchronization cancelled.")
            raise

        except InstagramRateLimitError as exc:
            self._catalog.finish_run(
                run_id,
                result.downloaded,
                result.skipped,
                "failed",
                str(exc),
            )
            status(str(exc))
            raise

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
