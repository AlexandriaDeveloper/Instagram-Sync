from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import instaloader

from .database import MediaKey
from .paths import session_dir


@dataclass(frozen=True)
class RemoteMedia:
    key: MediaKey
    url: str
    media_type: str
    post_date: str | None
    extension: str


class InstagramClient:
    def __init__(self, username: str | None = None):
        self.username = (username or "").strip()
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True,
        )
        if self.username:
            self._try_load_session()

    def _session_file(self) -> Path:
        return session_dir() / f"{self.username}.session"

    def _try_load_session(self) -> bool:
        path = self._session_file()
        if not path.exists():
            return False
        self.loader.load_session_from_file(self.username, filename=str(path))
        return True

    def save_session(self) -> Path:
        if not self.username:
            raise ValueError("Instagram username is required to save a session.")
        path = self._session_file()
        self.loader.save_session_to_file(filename=str(path))
        return path

    def iter_profile_media(
        self,
        profile_name: str,
        include_posts: bool = True,
        include_reels: bool = True,
    ) -> Iterator[RemoteMedia]:
        profile = instaloader.Profile.from_username(self.loader.context, profile_name)

        if include_posts:
            for post in profile.get_posts():
                yield from self._post_media(post)

        if include_reels:
            for post in profile.get_reels():
                yield from self._post_media(post)

    def _post_media(self, post: instaloader.Post) -> Iterator[RemoteMedia]:
        post_date = post.date_utc.isoformat() if post.date_utc else None

        if post.typename == "GraphSidecar":
            for idx, node in enumerate(post.get_sidecar_nodes()):
                if node.is_video:
                    yield RemoteMedia(
                        MediaKey(post.shortcode, idx),
                        node.video_url,
                        "video",
                        post_date,
                        ".mp4",
                    )
                else:
                    yield RemoteMedia(
                        MediaKey(post.shortcode, idx),
                        node.display_url,
                        "image",
                        post_date,
                        ".jpg",
                    )
            return

        if post.is_video:
            yield RemoteMedia(
                MediaKey(post.shortcode, 0),
                post.video_url,
                "video",
                post_date,
                ".mp4",
            )
        else:
            yield RemoteMedia(
                MediaKey(post.shortcode, 0),
                post.url,
                "image",
                post_date,
                ".jpg",
            )
