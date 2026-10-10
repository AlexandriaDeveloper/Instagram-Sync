from instagram_sync.database import MediaKey
from instagram_sync.instagram_client import RemoteMedia
from instagram_sync.sync_service import SyncService

def test_filename_is_stable():
    media = RemoteMedia(
        key=MediaKey("SHORTCODE", 3),
        url="https://example.invalid/x",
        media_type="video",
        post_date=None,
        extension=".mp4",
    )
    assert SyncService._filename(media) == "SHORTCODE_03.mp4"
