"""Use Case لإدارة حالة Session المحلية بدون ربط الواجهة بنظام الملفات."""

from instagram_sync.application.ports import SessionStore


class ManageSessionUseCase:
    """الاستعلام عن Session وحذفها عبر Port قابل للاستبدال والاختبار."""

    def __init__(self, store: SessionStore) -> None:
        """حقن مخزن الـSession للحفاظ على Dependency Inversion."""
        self._store = store

    def is_connected(self, username: str) -> bool:
        """التحقق من وجود Session محلية لاسم مستخدم صالح."""
        normalized = username.strip()
        return bool(normalized) and self._store.exists(normalized)

    def disconnect(self, username: str) -> None:
        """حذف Session المحلية إن كان اسم المستخدم موجودًا."""
        normalized = username.strip()
        if normalized:
            self._store.remove(normalized)
