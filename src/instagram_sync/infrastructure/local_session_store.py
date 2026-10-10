"""Adapter محلي لإدارة ملفات Session الخاصة بالتطبيق."""

from instagram_sync.paths import session_path


class LocalSessionStore:
    """تنفيذ SessionStore باستخدام مجلد بيانات التطبيق المحلي."""

    def exists(self, username: str) -> bool:
        """التحقق من وجود ملف Session للحساب."""
        return session_path(username).exists()

    def remove(self, username: str) -> None:
        """حذف ملف Session فقط بدون التأثير على حساب Instagram."""
        session_path(username).unlink(missing_ok=True)
