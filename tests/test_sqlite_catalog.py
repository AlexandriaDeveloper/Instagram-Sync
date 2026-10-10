"""اختبار Adapter الخاص بـSQLite."""

from pathlib import Path

from instagram_sync.domain.models import MediaIdentity, RemoteMedia
from instagram_sync.infrastructure.sqlite_catalog import SQLiteMediaCatalog


def test_catalog_records_media_once(tmp_path: Path) -> None:
    """UNIQUE constraint يجب أن يمنع تسجيل نفس العنصر مرتين."""
    catalog = SQLiteMediaCatalog(
        tmp_path / "catalog.sqlite3"
    )
    media = RemoteMedia(
        identity=MediaIdentity("ABC123", 0),
        url="https://example.invalid/a",
        media_type="image",
        post_date=None,
        extension=".jpg",
    )

    assert catalog.contains("example", media.identity) is False

    catalog.record_media(
        "example",
        media,
        "ABC123_00.jpg",
    )
    catalog.record_media(
        "example",
        media,
        "ABC123_00.jpg",
    )

    assert catalog.contains("example", media.identity) is True
    assert catalog.profile_count("example") == 1
