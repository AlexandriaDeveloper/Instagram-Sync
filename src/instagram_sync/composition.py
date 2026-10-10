"""Composition Root.

هذا هو المكان الوحيد الذي يربط Use Cases بالـAdapters الحقيقية.
"""

from instagram_sync.application.connect_session import ConnectBrowserSessionUseCase
from instagram_sync.application.sync_profile import SyncProfileUseCase
from instagram_sync.application.sync_watch_list import SyncWatchListUseCase
from instagram_sync.application.watch_list import ManageWatchListUseCase
from instagram_sync.infrastructure.browser_session import (
    InstaloaderBrowserSessionImporter,
)
from instagram_sync.infrastructure.http_downloader import UrlLibBinaryDownloader
from instagram_sync.infrastructure.instagram_source import InstaloaderMediaSource
from instagram_sync.infrastructure.sqlite_catalog import SQLiteMediaCatalog
from instagram_sync.infrastructure.sqlite_watch_list import SQLiteWatchListRepository
from instagram_sync.paths import database_path


def build_sync_use_case(username: str | None = None) -> SyncProfileUseCase:
    """تجميع Dependencies الخاصة بمزامنة حساب واحد."""
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


def build_watch_list_use_case() -> ManageWatchListUseCase:
    """تجميع Dependencies الخاصة بإدارة Watch List."""
    return ManageWatchListUseCase(
        repository=SQLiteWatchListRepository(database_path()),
    )


def build_watch_sync_use_case(
    username: str | None = None,
) -> SyncWatchListUseCase:
    """تجميع مزامنة Watch List لمرة واحدة."""
    return SyncWatchListUseCase(
        repository=SQLiteWatchListRepository(database_path()),
        sync_executor=build_sync_use_case(username),
    )
