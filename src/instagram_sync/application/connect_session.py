"""Use Case مسؤول فقط عن إنشاء Session من المتصفح."""

from instagram_sync.application.ports import BrowserSessionImporter
from instagram_sync.domain.models import SessionInfo


class ConnectBrowserSessionUseCase:
    """واجهة Application نظيفة لاستيراد Session."""

    def __init__(self, importer: BrowserSessionImporter) -> None:
        """حقن Adapter المتصفح بدل ربط الواجهة مباشرة بمكتبة خارجية."""
        self._importer = importer

    def execute(self, browser: str) -> SessionInfo:
        """التحقق من اسم المتصفح ثم بدء الاستيراد."""
        normalized = browser.strip().lower()
        if not normalized:
            raise ValueError("Choose a browser first.")
        return self._importer.import_session(normalized)
