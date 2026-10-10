"""Use Case لمزامنة Watch List مرة واحدة عند فتح البرنامج أو يدويًا."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from instagram_sync.application.ports import ProfileSyncExecutor, WatchListRepository
from instagram_sync.domain.models import SyncRequest, WatchSyncSummary


class SyncWatchListUseCase:
    """يمر على الحسابات المختارة فقط ويشغّل Incremental Sync لكل واحد."""

    def __init__(
        self,
        repository: WatchListRepository,
        sync_executor: ProfileSyncExecutor,
    ) -> None:
        """حقن Repository ومنفذ المزامنة لتحقيق Dependency Inversion."""
        self._repository = repository
        self._sync_executor = sync_executor

    def execute(
        self,
        destination: Path,
        on_status: Callable[[str], None] | None = None,
        on_progress: Callable[[int, int], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> WatchSyncSummary:
        """عمل Check واحد لكل Watch List بدون أي Polling دوري."""
        summary = WatchSyncSummary()

        def status(message: str) -> None:
            """تمرير Progress للواجهة."""
            if on_status:
                on_status(message)

        for watched in self._repository.list_profiles():
            if should_cancel and should_cancel():
                break

            summary.checked_profiles += 1
            status(f"Checking watched profile @{watched.profile}...")

            try:
                result = self._sync_executor.execute(
                    SyncRequest(
                        profile=watched.profile,
                        destination=destination,
                    ),
                    on_status=on_status,
                    on_progress=on_progress,
                    should_cancel=should_cancel,
                )
                summary.downloaded += result.downloaded
                summary.skipped += result.skipped
                self._repository.mark_checked(watched.profile)
            # فصل فشل حساب واحد عن باقي القائمة مقصود حتى لا تتوقف Watch List كلها.
            except Exception as exc:  # noqa: BLE001
                summary.failed_profiles += 1
                status(f"Watch sync failed for @{watched.profile}: {exc}")

        return summary
