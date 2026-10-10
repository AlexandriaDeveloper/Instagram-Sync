"""Adapter لقراءة Posts وReels باستخدام Instaloader."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from concurrent.futures import CancelledError

import instaloader

from instagram_sync.domain.models import MediaIdentity, RemoteMedia
from instagram_sync.paths import session_path

_CANCEL_MESSAGE = "Synchronization cancelled."


class _CancellableRateController(instaloader.RateController):
    """Rate controller يسمح بإيقاف انتظار Instagram عند طلب الإلغاء."""

    def __init__(
        self,
        context: instaloader.InstaloaderContext,
        should_cancel: Callable[[], bool],
    ) -> None:
        super().__init__(context)
        self._should_cancel = should_cancel

    def sleep(self, secs: float) -> None:
        """تقسيم الانتظار لفترات قصيرة حتى يظل زر Cancel مستجيبًا."""
        deadline = time.monotonic() + secs
        while True:
            if self._should_cancel():
                raise CancelledError(_CANCEL_MESSAGE)

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return

            time.sleep(min(0.25, remaining))


class InstaloaderMediaSource:
    """قراءة المحتوى العام أو الخاص الذي تسمح به Session الحالية."""

    def __init__(self, username: str | None = None) -> None:
        """إنشاء Client وتحميل Session محلية عند وجود حساب متصل."""
        self._username = (username or "").strip().lower()
        self._should_cancel: Callable[[], bool] = lambda: False
        self._loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True,
            max_connection_attempts=1,
            request_timeout=15.0,
            rate_controller=lambda context: _CancellableRateController(
                context,
                lambda: self._should_cancel(),
            ),
        )

        if self._username:
            self._load_saved_session()

    def _load_saved_session(self) -> None:
        """تحميل Session فقط لو ملفها موجود محليًا."""
        path = session_path(self._username)
        if not path.exists():
            return

        self._loader.load_session_from_file(
            self._username,
            filename=str(path),
        )

    def iter_profile_media(
        self,
        profile_name: str,
        include_posts: bool = True,
        include_reels: bool = True,
        should_cancel: Callable[[], bool] | None = None,
    ) -> Iterator[RemoteMedia]:
        """إرجاع Media مع فحص الإلغاء أثناء مرحلة الحصر نفسها."""
        self._should_cancel = should_cancel or (lambda: False)

        try:
            self._raise_if_cancelled()
            profile = instaloader.Profile.from_username(
                self._loader.context,
                profile_name,
            )

            if include_posts:
                yield from self._iter_posts(iter(profile.get_posts()))

            if include_reels:
                yield from self._iter_posts(iter(profile.get_reels()))
        finally:
            self._should_cancel = lambda: False

    def _iter_posts(
        self,
        posts: Iterator[instaloader.Post],
    ) -> Iterator[RemoteMedia]:
        """قراءة الـPosts مع نقطة إلغاء قبل وبعد كل طلب للعنصر التالي."""
        while True:
            self._raise_if_cancelled()
            try:
                post = next(posts)
            except StopIteration:
                return

            self._raise_if_cancelled()
            yield from self._post_media(post)

    def _post_media(self, post: instaloader.Post) -> Iterator[RemoteMedia]:
        """تحويل Post واحد، بما فيه Carousel، إلى عناصر مستقلة."""
        self._raise_if_cancelled()
        post_date = post.date_utc.isoformat() if post.date_utc else None

        if post.typename == "GraphSidecar":
            for index, node in enumerate(post.get_sidecar_nodes()):
                self._raise_if_cancelled()
                if node.is_video:
                    yield RemoteMedia(
                        identity=MediaIdentity(post.shortcode, index),
                        url=node.video_url,
                        media_type="video",
                        post_date=post_date,
                        extension=".mp4",
                    )
                else:
                    yield RemoteMedia(
                        identity=MediaIdentity(post.shortcode, index),
                        url=node.display_url,
                        media_type="image",
                        post_date=post_date,
                        extension=".jpg",
                    )
            return

        self._raise_if_cancelled()
        if post.is_video:
            yield RemoteMedia(
                identity=MediaIdentity(post.shortcode, 0),
                url=post.video_url,
                media_type="video",
                post_date=post_date,
                extension=".mp4",
            )
        else:
            yield RemoteMedia(
                identity=MediaIdentity(post.shortcode, 0),
                url=post.url,
                media_type="image",
                post_date=post_date,
                extension=".jpg",
            )

    def _raise_if_cancelled(self) -> None:
        """تحويل طلب الإلغاء إلى استثناء قياسي يصل للـWorker."""
        if self._should_cancel():
            raise CancelledError(_CANCEL_MESSAGE)
