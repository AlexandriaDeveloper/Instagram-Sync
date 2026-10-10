from instagram_sync.database import MediaDatabase, MediaKey

def test_media_is_recorded_once(tmp_path):
    db = MediaDatabase(tmp_path / "test.sqlite3")
    key = MediaKey("ABC123", 0)

    assert db.contains("Example", key) is False

    db.record_media(
        profile="Example",
        key=key,
        media_type="image",
        post_date="2026-01-01T00:00:00",
        filename="ABC123_00.jpg",
    )
    db.record_media(
        profile="Example",
        key=key,
        media_type="image",
        post_date="2026-01-01T00:00:00",
        filename="ABC123_00.jpg",
    )

    assert db.contains("example", key) is True
    assert db.profile_count("EXAMPLE") == 1
