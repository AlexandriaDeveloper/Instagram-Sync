"""Composition Root.

هذا هو المكان الوحيد الذي يربط Use Cases بالـAdapters الحقيقية.
"""

from instagram_sync.application.connect_session import ConnectBrowserSessionUseCase
from instagram_sync.application.sync_profile import SyncProfileUseCase
from instagram_sync.infrastructure.browser_session import (
    InstaloaderBrowserSessionImporter,
)
from instagram_sync.infrastructure.http_downloader import UrlLibBinaryDownloader
from instagram_sync.infrastructure.instagram_source import InstaloaderMediaSource
from instagram_sync.infrastructure.sqlite_catalog import SQLiteMediaCatalog
from instagram_sync.paths import database_path


def build_sync_use_case(username: str | None = None) -> SyncProfileUseCase:
    """تجميع Dependencies الخاصة بالمزامنة في نقطة مركزية."""
    return SyncProfileUseCase(
        source=InstaloaderMediaSource(username),
        catalog=SQLiteMediaCatalog(database_path()),
        downloader=UrlLibBinaryDownloader(),
    )


def build_connect_session_use_case() -> ConnectBrowserSessionUseCase:
    """تجميع Dependencies الخاصة باستيراد Session من المتصفح."""
    return ConnectBrowserSessionUseCase(
        importer=InstaloaderBrowserSessionImporter(),
    )
