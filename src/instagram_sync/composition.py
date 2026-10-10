"""Composition Root.

هذا هو المكان الوحيد الذي يربط Use Cases بالـAdapters الحقيقية.
"""

from instagram_sync.application.sync_profile import SyncProfileUseCase
from instagram_sync.application.sync_watch_list import SyncWatchListUseCase
from instagram_sync.application.watch_list import ManageWatchListUseCase
from instagram_sync.infrastructure.http_downloader import UrlLibBinaryDownloader
from instagram_sync.infrastructure.instagram_source import InstaloaderMediaSource
from instagram_sync.infrastructure.sqlite_catalog import SQLiteMediaCatalog
from instagram_sync.infrastructure.sqlite_watch_list import SQLiteWatchListRepository
from instagram_sync.paths import database_path


def build_sync_use_case() -> SyncProfileUseCase:
    """تجميع Dependencies الخاصة بمزامنة حساب واحد."""
    return SyncProfileUseCase(
        source=InstaloaderMediaSource(),
        catalog=SQLiteMediaCatalog(database_path()),
        downloader=UrlLibBinaryDownloader(),
    )


def build_watch_list_use_case() -> ManageWatchListUseCase:
    """تجميع Dependencies الخاصة بإدارة Watch List."""
    return ManageWatchListUseCase(
        repository=SQLiteWatchListRepository(database_path()),
    )


def build_watch_sync_use_case() -> SyncWatchListUseCase:
    """تجميع مزامنة Watch List لمرة واحدة."""
    return SyncWatchListUseCase(
        repository=SQLiteWatchListRepository(database_path()),
        sync_executor=build_sync_use_case(),
    )
