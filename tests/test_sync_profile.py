"""اختبارات Use Case بدون شبكة أو Instagram حقيقي."""

from pathlib import Path

import pytest

from instagram_sync.application.sync_profile import SyncProfileUseCase
from instagram_sync.domain.models import MediaIdentity, RemoteMedia, SyncRequest


class FakeSource:
    """مصدر وهمي يجعل الاختبار Deterministic."""

    def __init__(self, media: list[RemoteMedia]) -> None:
        self.media = list(media)

    def iter_profile_media(
        self,
        profile_name: str,
        include_posts: bool = True,
        include_reels: bool = True,
    ):
        return iter(self.media)


class FakeCatalog:
    """Catalog في الذاكرة لاختبار التكرار."""

    def __init__(self) -> None:
        self.items: set[tuple[str, str, int]] = set()
        self.run_id = 0

    def contains(self, profile: str, identity: MediaIdentity) -> bool:
        return (
            profile,
            identity.shortcode,
            identity.item_index,
        ) in self.items

    def record_media(
        self,
        profile: str,
        media: RemoteMedia,
        filename: str,
    ) -> None:
        self.items.add(
            (
                profile,
                media.identity.shortcode,
                media.identity.item_index,
            )
        )

    def start_run(self, profile: str) -> int:
        self.run_id += 1
        return self.run_id

    def finish_run(
        self,
        run_id: int,
        downloaded: int,
        skipped: int,
        status: str,
        error: str | None = None,
    ) -> None:
        return None


class FakeDownloader:
    """Downloader وهمي يسجل المسارات بدل استخدام الإنترنت."""

    def __init__(self) -> None:
        self.paths: list[Path] = []

    def download(self, url: str, path: Path) -> None:
        self.paths.append(path)


def test_second_sync_skips_existing_media(tmp_path: Path) -> None:
    """المزامنة الثانية يجب ألا تعيد تنزيل العناصر القديمة."""
    media = [
        RemoteMedia(
            identity=MediaIdentity("AAA", 0),
            url="https://example.invalid/a",
            media_type="image",
            post_date=None,
            extension=".jpg",
        ),
        RemoteMedia(
            identity=MediaIdentity("BBB", 0),
            url="https://example.invalid/b",
            media_type="video",
            post_date=None,
            extension=".mp4",
        ),
    ]

    source = FakeSource(media)
    catalog = FakeCatalog()
    downloader = FakeDownloader()
    use_case = SyncProfileUseCase(
        source,
        catalog,
        downloader,
    )
    request = SyncRequest(
        "Example.User",
        tmp_path,
    )

    first = use_case.execute(request)
    second = use_case.execute(request)

    assert first.downloaded == 2
    assert first.skipped == 0
    assert second.downloaded == 0
    assert second.skipped == 2
    assert len(downloader.paths) == 2


@pytest.mark.parametrize(
    "profile",
    [
        "../escape",
        "bad/name",
        "bad\\name",
        "has space",
        "x" * 31,
    ],
)
def test_invalid_profile_names_are_rejected(
    tmp_path: Path,
    profile: str,
) -> None:
    """منع أسماء قد تستخدم كمسارات أو لا تطابق صيغة Username."""
    use_case = SyncProfileUseCase(
        FakeSource([]),
        FakeCatalog(),
        FakeDownloader(),
    )

    with pytest.raises(
        ValueError,
        match="Invalid Instagram profile name",
    ):
        use_case.execute(
            SyncRequest(profile, tmp_path)
        )
