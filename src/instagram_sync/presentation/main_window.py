"""النافذة الرئيسية للتطبيق.

الواجهة تجمع Input وتعرض Progress فقط؛ منطق المزامنة موجود في Application Layer.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from instagram_sync.composition import (
    build_connect_session_use_case,
    build_sync_use_case,
)
from instagram_sync.domain.models import SyncRequest


class SyncWorker(QThread):
    """تشغيل Sync خارج UI Thread حتى لا تتجمد النافذة."""

    status = Signal(str)
    completed = Signal(int, int)
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
                should_cancel=lambda: self._cancelled,
            )
            self.completed.emit(result.downloaded, result.skipped)
        except Exception as exc:
            self.failed.emit(str(exc))


class SessionWorker(QThread):
    """استيراد Session قد يقرأ ملفات المتصفح لذلك يعمل خارج UI Thread."""

    completed = Signal(str, str)
    failed = Signal(str)

    def __init__(self, browser: str) -> None:
        """حفظ اسم المتصفح المختار."""
        super().__init__()
        self._browser = browser

    def run(self) -> None:
        """استيراد Session وإرجاع اسم المستخدم الحقيقي المكتشف."""
        try:
            use_case = build_connect_session_use_case()
            info = use_case.execute(self._browser)
            self.completed.emit(info.username, info.browser)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    """واجهة التطبيق الرئيسية."""

    _SUPPORTED_BROWSERS = [
        "Chrome",
        "Edge",
        "Firefox",
        "Brave",
        "Chromium",
        "LibreWolf",
        "Opera",
        "Opera_GX",
        "Vivaldi",
    ]

    def __init__(self) -> None:
        """إنشاء الواجهة وتحميل الإعدادات المحلية."""
        super().__init__()
        self.setWindowTitle("Instagram Sync")
        self.resize(760, 620)

        self._settings = QSettings(
            "AlexandriaDeveloper",
            "InstagramSync",
        )
        self._sync_worker: SyncWorker | None = None
        self._session_worker: SessionWorker | None = None

        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        """بناء Controls وترتيبها بدون أي Business Logic."""
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        layout.addWidget(QLabel("<h2>Instagram Sync</h2>"))
        layout.addWidget(
            QLabel("Download once, then sync only media that is not already stored.")
        )

        form = QFormLayout()

        self._profile = QLineEdit()
        self._profile.setPlaceholderText("target_profile")
        form.addRow("Target profile:", self._profile)

        self._username = QLineEdit()
        self._username.setReadOnly(True)
        self._username.setPlaceholderText("No saved Instagram session")
        form.addRow("Connected account:", self._username)

        browser_row = QHBoxLayout()
        self._browser = QComboBox()
        self._browser.addItems(self._SUPPORTED_BROWSERS)
        self._connect_button = QPushButton("Connect from Browser")
        self._connect_button.clicked.connect(self._connect_from_browser)
        browser_row.addWidget(self._browser)
        browser_row.addWidget(self._connect_button)
        form.addRow("Browser session:", browser_row)

        destination_row = QHBoxLayout()
        self._destination = QLineEdit()
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse)
        destination_row.addWidget(self._destination)
        destination_row.addWidget(browse_button)
        form.addRow("Download folder:", destination_row)

        layout.addLayout(form)

        options = QHBoxLayout()
        self._posts = QCheckBox("Posts")
        self._posts.setChecked(True)
        self._reels = QCheckBox("Reels")
        self._reels.setChecked(True)
        options.addWidget(self._posts)
        options.addWidget(self._reels)
        options.addStretch()
        layout.addLayout(options)

        actions = QHBoxLayout()
        self._sync_button = QPushButton("Sync Now")
        self._sync_button.clicked.connect(self._start_sync)
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setEnabled(False)
        self._cancel_button.clicked.connect(self._cancel_sync)
        actions.addWidget(self._sync_button)
        actions.addWidget(self._cancel_button)
        actions.addStretch()
        layout.addLayout(actions)

        self._progress = QProgressBar()
        self._progress.setRange(0, 1)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        layout.addWidget(self._log)

    def _load_settings(self) -> None:
        """استرجاع الإعدادات غير الحساسة فقط."""
        self._username.setText(
            self._settings.value("username", "", str)
        )

        default_destination = str(
            Path.home() / "Downloads" / "InstagramSync"
        )
        self._destination.setText(
            self._settings.value(
                "destination",
                default_destination,
                str,
            )
        )

        saved_browser = self._settings.value(
            "browser",
            "Chrome",
            str,
        )
        browser_index = self._browser.findText(saved_browser)
        if browser_index >= 0:
            self._browser.setCurrentIndex(browser_index)

    def _save_settings(self) -> None:
        """حفظ اسم المستخدم المكتشف والمسار والمتصفح فقط؛ لا Cookies ولا Password."""
        self._settings.setValue(
            "username",
            self._username.text().strip(),
        )
        self._settings.setValue(
            "destination",
            self._destination.text().strip(),
        )
        self._settings.setValue(
            "browser",
            self._browser.currentText(),
        )

    def _browse(self) -> None:
        """فتح اختيار مجلد التنزيل."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose download folder",
            self._destination.text(),
        )
        if folder:
            self._destination.setText(folder)

    def _connect_from_browser(self) -> None:
        """بدء استيراد Session من المتصفح بدون طلب Password."""
        if self._session_worker and self._session_worker.isRunning():
            return

        self._connect_button.setEnabled(False)
        self._log.append(
            "Reading Instagram session from the selected browser..."
        )

        self._session_worker = SessionWorker(
            self._browser.currentText(),
        )
        self._session_worker.completed.connect(
            self._session_connected,
        )
        self._session_worker.failed.connect(
            self._session_failed,
        )
        self._session_worker.start()

    def _session_connected(
        self,
        username: str,
        browser: str,
    ) -> None:
        """تحديث الواجهة بعد نجاح استيراد Session."""
        self._connect_button.setEnabled(True)
        self._username.setText(username)
        self._save_settings()
        self._log.append(
            f"Connected as @{username} using {browser}."
        )
        QMessageBox.information(
            self,
            "Instagram session connected",
            f"Connected as @{username}.",
        )

    def _session_failed(self, message: str) -> None:
        """عرض سبب فشل Session بدون كشف بيانات حساسة."""
        self._connect_button.setEnabled(True)
        self._log.append(f"SESSION ERROR: {message}")
        QMessageBox.critical(
            self,
            "Session connection failed",
            message,
        )

    def _start_sync(self) -> None:
        """التحقق من Input ثم بدء Worker للمزامنة."""
        profile = self._profile.text().strip()
        destination = self._destination.text().strip()

        if not profile or not destination:
            QMessageBox.warning(
                self,
                "Missing information",
                "Enter a target profile and download folder.",
            )
            return

        if not self._posts.isChecked() and not self._reels.isChecked():
            QMessageBox.warning(
                self,
                "Nothing selected",
                "Select Posts and/or Reels.",
            )
            return

        self._save_settings()
        self._log.clear()
        self._sync_button.setEnabled(False)
        self._cancel_button.setEnabled(True)

        # Range 0,0 يجعل QProgressBar في وضع Busy لأن العدد الكلي غير معروف مسبقًا.
        self._progress.setRange(0, 0)

        request = SyncRequest(
            profile=profile,
            destination=Path(destination),
            include_posts=self._posts.isChecked(),
            include_reels=self._reels.isChecked(),
        )

        self._sync_worker = SyncWorker(
            request=request,
            username=self._username.text().strip(),
        )
        self._sync_worker.status.connect(self._log.append)
        self._sync_worker.completed.connect(self._sync_completed)
        self._sync_worker.failed.connect(self._sync_failed)
        self._sync_worker.start()

    def _cancel_sync(self) -> None:
        """طلب إلغاء آمن بدل إنهاء Thread بالقوة."""
        if self._sync_worker:
            self._sync_worker.cancel()
            self._log.append("Cancellation requested...")

    def _finish_sync_ui(self) -> None:
        """إعادة Controls لحالتها الطبيعية بعد نجاح أو فشل."""
        self._sync_button.setEnabled(True)
        self._cancel_button.setEnabled(False)
        self._progress.setRange(0, 1)
        self._progress.setValue(1)

    def _sync_completed(
        self,
        downloaded: int,
        skipped: int,
    ) -> None:
        """عرض أرقام المزامنة النهائية."""
        self._finish_sync_ui()
        QMessageBox.information(
            self,
            "Sync complete",
            (
                f"Downloaded: {downloaded}\n"
                f"Already present: {skipped}"
            ),
        )

    def _sync_failed(self, message: str) -> None:
        """عرض الخطأ مع إبقائه في Log للمراجعة."""
        self._finish_sync_ui()
        self._log.append(f"ERROR: {message}")
        QMessageBox.critical(
            self,
            "Sync failed",
            message,
        )


def run_app() -> int:
    """إنشاء QApplication ثم عرض النافذة الرئيسية."""
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()
