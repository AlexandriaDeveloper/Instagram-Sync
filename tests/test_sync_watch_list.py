"""اختبار Startup Watch Sync بدون Instagram حقيقي."""

from pathlib import Path

from instagram_sync.application.sync_watch_list import SyncWatchListUseCase
from instagram_sync.domain.models import (
    SyncRequest,
    SyncResult,
    WatchProfile,
)


class FakeWatchRepository:
    """Repository يعيد فقط الحسابات التي اختارها المستخدم."""

    def __init__(self) -> None:
        self.items = [
            WatchProfile("alpha"),
            WatchProfile("beta"),
        ]
        self.checked: list[str] = []

    def list_profiles(self) -> list[WatchProfile]:
        return self.items

    def add_profile(self, profile: str) -> None:
        return None

    def remove_profile(self, profile: str) -> None:
        return None

    def mark_checked(self, profile: str) -> None:
        self.checked.append(profile)


class FakeSyncExecutor:
    """منفذ مزامنة وهمي يسجل الحسابات التي تم فحصها."""

    def __init__(self) -> None:
        self.profiles: list[str] = []

    def execute(
        self,
        request: SyncRequest,
        on_status=None,
        should_cancel=None,
    ) -> SyncResult:
        self.profiles.append(request.profile)
        return SyncResult(downloaded=1, skipped=2)


def test_watch_sync_runs_only_for_watch_list(tmp_path: Path) -> None:
    """لا يجب مزامنة أي حساب غير موجود في Watch List."""
    repository = FakeWatchRepository()
    sync_executor = FakeSyncExecutor()
    use_case = SyncWatchListUseCase(
        repository,
        sync_executor,
    )

    summary = use_case.execute(tmp_path)

    assert sync_executor.profiles == ["alpha", "beta"]
    assert repository.checked == ["alpha", "beta"]
    assert summary.checked_profiles == 2
    assert summary.downloaded == 2
    assert summary.skipped == 4
    assert summary.failed_profiles == 0
