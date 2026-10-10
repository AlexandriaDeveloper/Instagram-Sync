"""Adapter لقراءة Posts وReels باستخدام Instaloader."""

from __future__ import annotations

from collections.abc import Iterator

import instaloader

from instagram_sync.domain.models import MediaIdentity, RemoteMedia
from instagram_sync.paths import session_path


class InstaloaderMediaSource:
    """تحويل Objects الخاصة بـInstaloader إلى Domain Models بسيطة."""

    def __init__(self, username: str | None = None) -> None:
        """إنشاء Instaloader وتحميل Session محلية إن كانت موجودة."""
        self._username = (username or "").strip().lower()
        self._loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True,
        )

        if self._username:
            self._try_load_session()

    def _try_load_session(self) -> bool:
        """تحميل Session المحفوظة سابقًا؛ لا يتم طلب Password."""
        path = session_path(self._username)
        if not path.exists():
            return False

        self._loader.load_session_from_file(
            self._username,
            filename=str(path),
        )
        return True

    def iter_profile_media(
        self,
        profile_name: str,
        include_posts: bool = True,
        include_reels: bool = True,
    ) -> Iterator[RemoteMedia]:
        """إرجاع Media المتاحة للحساب حسب صلاحية Session الحالية."""
        profile = instaloader.Profile.from_username(
            self._loader.context,
            profile_name,
        )

        if include_posts:
            for post in profile.get_posts():
                yield from self._post_media(post)

        if include_reels:
            for post in profile.get_reels():
                yield from self._post_media(post)

    @staticmethod
    def _post_media(post: instaloader.Post) -> Iterator[RemoteMedia]:
        """تحويل Post واحد، بما فيه Carousel، إلى عناصر مستقلة."""
        post_date = post.date_utc.isoformat() if post.date_utc else None

        if post.typename == "GraphSidecar":
            for index, node in enumerate(post.get_sidecar_nodes()):
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
