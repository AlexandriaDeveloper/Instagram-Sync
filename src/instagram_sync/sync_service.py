from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

from .database import MediaDatabase
from .instagram_client import InstagramClient, RemoteMedia


@dataclass
class SyncResult:
    downloaded: int = 0
    skipped: int = 0


class SyncCancelled(Exception):
    pass


class SyncService:
    def __init__(self, database: MediaDatabase, client: InstagramClient):
        self.database = database
        self.client = client

    def sync(
        self,
        profile: str,
        destination: Path,
        include_posts: bool = True,
        include_reels: bool = True,
        on_status: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> SyncResult:
        destination.mkdir(parents=True, exist_ok=True)
        profile_dir = destination / profile.lower()
        profile_dir.mkdir(parents=True, exist_ok=True)

        run_id = self.database.start_run(profile)
        result = SyncResult()

        def status(message: str) -> None:
            if on_status:
                on_status(message)

        try:
            status(f"Reading @{profile}...")
            for remote in self.client.iter_profile_media(profile, include_posts, include_reels):
                if should_cancel and should_cancel():
                    raise SyncCancelled("Synchronization cancelled.")

                if self.database.contains(profile, remote.key):
                    result.skipped += 1
                    continue

                filename = self._filename(remote)
                path = profile_dir / filename
                status(f"Downloading {filename}")
                self._download(remote.url, path)
                self.database.record_media(
                    profile=profile,
                    key=remote.key,
                    media_type=remote.media_type,
                    post_date=remote.post_date,
                    filename=str(path),
                )
                result.downloaded += 1

            self.database.finish_run(
                run_id, result.downloaded, result.skipped, "success"
            )
            status(
                f"Done. Downloaded {result.downloaded}, skipped {result.skipped}."
            )
            return result
        except Exception as exc:
            self.database.finish_run(
                run_id, result.downloaded, result.skipped, "failed", str(exc)
            )
            raise

    @staticmethod
    def _filename(remote: RemoteMedia) -> str:
        return f"{remote.key.shortcode}_{remote.key.item_index:02d}{remote.extension}"

    @staticmethod
    def _download(url: str, path: Path) -> None:
        temp_path = path.with_suffix(path.suffix + ".part")
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/126 Safari/537.36"
                )
            },
        )
        try:
            with urlopen(request, timeout=60) as response, temp_path.open("wb") as out:
                while chunk := response.read(1024 * 1024):
                    out.write(chunk)
            temp_path.replace(path)
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
