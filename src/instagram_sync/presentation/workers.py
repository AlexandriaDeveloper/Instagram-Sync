"""Workers الخاصة بالمزامنة بعيدًا عن UI Thread."""

from __future__ import annotations

from concurrent.futures import CancelledError
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from instagram_sync.composition import build_sync_use_case, build_watch_sync_use_case
from instagram_sync.domain.models import SyncRequest


class SyncWorker(QThread):
    """تشغيل Sync لحساب واحد خارج UI Thread."""

    status = Signal(str)
    progress = Signal(int, int)
    completed = Signal(int, int)
    cancelled = Signal()
    failed = Signal(str)

    def __init__(
        self,
        request: SyncRequest,
        username: str,
    ) -> None:
        """حفظ مدخلات العملية فقط؛ الـUse Case ينشأ داخل الـThread."""
        super().__init__()
        self._request = request
        self._username = username
        self._cancelled = False

    def cancel(self) -> None:
        """تسجيل طلب الإلغاء ليتم التقاطه بين عناصر Media."""
        self._cancelled = True

    def run(self) -> None:
        """تنفيذ المزامنة وإرسال النتيجة للواجهة عبر Signals."""
        try:
            use_case = build_sync_use_case(self._username)
            result = use_case.execute(
                self._request,
                on_status=self.status.emit,
                on_progress=self.progress.emit,
                should_cancel=lambda: self._cancelled,
            )
            self.completed.emit(result.downloaded, result.skipped)
        except CancelledError:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001
            # هذا Boundary مقصود لتحويل أخطاء الشبكة أو Instagram إلى Signal للواجهة.
            self.failed.emit(str(exc))


class WatchSyncWorker(QThread):
    """عمل Check واحد للحسابات المختارة في Watch List."""

    status = Signal(str)
    progress = Signal(int, int)
    completed = Signal(int, int, int, int)
    cancelled = Signal()
    failed = Signal(str)

    def __init__(
        self,
        destination: Path,
        username: str,
    ) -> None:
        """حفظ إعدادات التشغيل بدون أي Polling داخلي."""
        super().__init__()
        self._destination = destination
        self._username = username
        self._cancelled = False

    def cancel(self) -> None:
        """طلب إلغاء بين الحسابات أو عناصر Media."""
        self._cancelled = True

    def run(self) -> None:
        """تنفيذ Check واحد فقط ثم إنهاء Thread."""
        try:
            use_case = build_watch_sync_use_case(self._username)
            summary = use_case.execute(
                destination=self._destination,
                on_status=self.status.emit,
                on_progress=self.progress.emit,
                should_cancel=lambda: self._cancelled,
            )
            self.completed.emit(
                summary.checked_profiles,
                summary.downloaded,
                summary.skipped,
                summary.failed_profiles,
            )
        except CancelledError:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001
            # منع فشل Thread بصمت وإرجاع الخطأ للواجهة بشكل موحد.
            self.failed.emit(str(exc))
