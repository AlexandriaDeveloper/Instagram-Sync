"""Use Case لإدارة الحسابات التي اختار المستخدم متابعتها."""

from instagram_sync.application.ports import WatchListRepository
from instagram_sync.application.profile_name import normalize_profile_name
from instagram_sync.domain.models import WatchProfile


class ManageWatchListUseCase:
    """إضافة وحذف وقراءة Watch List بدون معرفة SQLite."""

    def __init__(self, repository: WatchListRepository) -> None:
        """حقن Repository حتى تظل Application Layer مستقلة."""
        self._repository = repository

    def list_profiles(self) -> list[WatchProfile]:
        """إرجاع الحسابات المختارة فقط."""
        return self._repository.list_profiles()

    def add_profile(self, profile: str) -> None:
        """إضافة حساب بعد التحقق من اسمه."""
        self._repository.add_profile(normalize_profile_name(profile))

    def remove_profile(self, profile: str) -> None:
        """حذف حساب من Watch List فقط؛ لا يحذف الملفات التي سبق تنزيلها."""
        self._repository.remove_profile(normalize_profile_name(profile))
