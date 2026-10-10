"""Use Case لحفظ Session بعد تسجيل الدخول داخل متصفح التطبيق."""

from collections.abc import Mapping

from instagram_sync.application.ports import SessionWriter
from instagram_sync.domain.models import SessionInfo


class ConnectSessionUseCase:
    """تحويل Cookies الموثقة إلى Session محلية قابلة لإعادة الاستخدام."""

    def __init__(self, writer: SessionWriter) -> None:
        """حقن Adapter الحفظ للحفاظ على Dependency Inversion."""
        self._writer = writer

    def execute(
        self,
        cookies: Mapping[str, str],
    ) -> SessionInfo:
        """رفض أي Session بدون sessionid ثم تفويض التحقق للـAdapter."""
        if not cookies.get("sessionid"):
            raise ValueError("Instagram login is not complete yet.")

        return self._writer.save_from_cookies(cookies)
