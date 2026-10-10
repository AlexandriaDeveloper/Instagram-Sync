"""النافذة الرئيسية للتطبيق.

الواجهة تجمع Input وتعرض Progress فقط؛ منطق المزامنة موجود في Application Layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import QSettings, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from instagram_sync.composition import (
    build_connect_session_use_case,
    build_sync_use_case,
    build_watch_list_use_case,
    build_watch_sync_use_case,
)
from instagram_sync.domain.models import SyncRequest


class SyncWorker(QThread):
    """تشغيل Sync لحساب واحد خارج UI Thread."""

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
        # Worker boundary: إظهار أخطاء الشبكة أو Instagram بدل إنهاء Thread بصمت.
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class WatchSyncWorker(QThread):
    """عمل Check واحد للحسابات المختارة في Watch List."""

    status = Signal(str)
    completed = Signal(int, int, int, int)

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
        use_case = build_watch_sync_use_case(self._username)
        summary = use_case.execute(
            destination=self._destination,
            on_status=self.status.emit,
            should_cancel=lambda: self._cancelled,
        )
        self.completed.emit(
            summary.checked_profiles,
            summary.downloaded,
            summary.skipped,
            summary.failed_profiles,
        )


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
        # Worker boundary: أخطاء قراءة المتصفح يجب أن تظهر للمستخدم.
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    """واجهة التطبيق الرئيسية."""

    _SUPPORTED_BROWSERS: ClassVar[tuple[str, ...]] = (
        "Chrome",
        "Edge",
        "Firefox",
        "Brave",
        "Chromium",
        "LibreWolf",
        "Opera",
        "Opera_GX",
        "Vivaldi",
    )

    def __init__(self) -> None:
        """إنشاء الواجهة وتحميل الإعدادات ثم جدولة Check واحد عند الفتح."""
        super().__init__()
        self.setWindowTitle("Instagram Sync")
        self.resize(820, 720)

        self._settings = QSettings(
            "AlexandriaDeveloper",
            "InstagramSync",
        )
        self._sync_worker: SyncWorker | None = None
        self._watch_worker: WatchSyncWorker | None = None
        self._session_worker: SessionWorker | None = None

        self._build_ui()
        self._load_settings()
        self._refresh_watch_list()

        # One-shot فقط: لا يوجد Timer دوري ولا Polling كل عدة دقائق.
        QTimer.singleShot(1200, self._sync_watch_list_on_open)

    def _build_ui(self) -> None:
        """بناء Controls وترتيبها بدون Business Logic."""
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        layout.addWidget(QLabel("<h2>Instagram Sync</h2>"))
        layout.addWidget(
            QLabel(
                "Manual sync + one startup check for profiles you explicitly watch."
            )
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

        manual_actions = QHBoxLayout()
        self._sync_button = QPushButton("Sync This Profile")
        self._sync_button.clicked.connect(self._start_manual_sync)
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setEnabled(False)
        self._cancel_button.clicked.connect(self._cancel_active_sync)
        manual_actions.addWidget(self._sync_button)
        manual_actions.addWidget(self._cancel_button)
        manual_actions.addStretch()
        layout.addLayout(manual_actions)

        watch_group = QGroupBox("Watch List — checked once when the app opens")
        watch_layout = QVBoxLayout(watch_group)

        self._watch_list = QListWidget()
        watch_layout.addWidget(self._watch_list)

        watch_actions = QHBoxLayout()
        self._add_watch_button = QPushButton("Add Target to Watch List")
        self._add_watch_button.clicked.connect(self._add_target_to_watch_list)
        self._remove_watch_button = QPushButton("Remove Selected")
        self._remove_watch_button.clicked.connect(self._remove_selected_watch)
        self._check_watch_button = QPushButton("Check Watch List Now")
        self._check_watch_button.clicked.connect(self._start_watch_sync)
        watch_actions.addWidget(self._add_watch_button)
        watch_actions.addWidget(self._remove_watch_button)
        watch_actions.addWidget(self._check_watch_button)
        watch_layout.addLayout(watch_actions)

        layout.addWidget(watch_group)

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
        """حفظ بيانات غير حساسة فقط؛ لا Cookies ولا Password."""
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

    def _is_sync_running(self) -> bool:
        """منع تشغيل Manual Sync وWatch Sync في نفس الوقت."""
        manual_running = bool(
            self._sync_worker and self._sync_worker.isRunning()
        )
        watch_running = bool(
            self._watch_worker and self._watch_worker.isRunning()
        )
        return manual_running or watch_running

    def _set_sync_busy(self, busy: bool) -> None:
        """توحيد حالة الأزرار أثناء أي نوع من المزامنة."""
        self._sync_button.setEnabled(not busy)
        self._check_watch_button.setEnabled(not busy)
        self._add_watch_button.setEnabled(not busy)
        self._remove_watch_button.setEnabled(not busy)
        self._cancel_button.setEnabled(busy)

        if busy:
            self._progress.setRange(0, 0)
        else:
            self._progress.setRange(0, 1)
            self._progress.setValue(1)

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

    def _start_manual_sync(self) -> None:
        """مزامنة الحساب المكتوب يدويًا فقط."""
        if self._is_sync_running():
            return

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
        self._set_sync_busy(True)

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
        self._sync_worker.completed.connect(self._manual_sync_completed)
        self._sync_worker.failed.connect(self._sync_failed)
        self._sync_worker.start()

    def _add_target_to_watch_list(self) -> None:
        """إضافة Target الحالي للقائمة المختارة فقط."""
        try:
            use_case = build_watch_list_use_case()
            use_case.add_profile(self._profile.text())
            self._refresh_watch_list()
        except ValueError as exc:
            QMessageBox.warning(
                self,
                "Invalid profile",
                str(exc),
            )

    def _remove_selected_watch(self) -> None:
        """إزالة الحساب المحدد من Watch List بدون حذف ملفاته القديمة."""
        item = self._watch_list.currentItem()
        if item is None:
            return

        use_case = build_watch_list_use_case()
        use_case.remove_profile(item.data(1000))
        self._refresh_watch_list()

    def _refresh_watch_list(self) -> None:
        """إعادة تحميل Watch List من SQLite وعرض آخر Check."""
        use_case = build_watch_list_use_case()
        watched_profiles = use_case.list_profiles()

        self._watch_list.clear()
        for watched in watched_profiles:
            last_checked = watched.last_checked_at or "Never"
            label = f"@{watched.profile}    Last check: {last_checked}"
            self._watch_list.addItem(label)
            item = self._watch_list.item(self._watch_list.count() - 1)
            item.setData(1000, watched.profile)

    def _sync_watch_list_on_open(self) -> None:
        """تشغيل Check واحد عند فتح التطبيق فقط."""
        if self._is_sync_running():
            return

        use_case = build_watch_list_use_case()
        if not use_case.list_profiles():
            return

        self._log.append("Startup Watch List check started...")
        self._start_watch_sync()

    def _start_watch_sync(self) -> None:
        """تشغيل Check واحد لكل الحسابات المختارة، بدون Timer دوري."""
        if self._is_sync_running():
            return

        destination = self._destination.text().strip()
        if not destination:
            return

        self._save_settings()
        self._set_sync_busy(True)

        self._watch_worker = WatchSyncWorker(
            destination=Path(destination),
            username=self._username.text().strip(),
        )
        self._watch_worker.status.connect(self._log.append)
        self._watch_worker.completed.connect(self._watch_sync_completed)
        self._watch_worker.start()

    def _cancel_active_sync(self) -> None:
        """إلغاء نوع المزامنة الجاري حاليًا بطريقة تعاونية."""
        if self._sync_worker and self._sync_worker.isRunning():
            self._sync_worker.cancel()

        if self._watch_worker and self._watch_worker.isRunning():
            self._watch_worker.cancel()

        self._log.append("Cancellation requested...")

    def _manual_sync_completed(
        self,
        downloaded: int,
        skipped: int,
    ) -> None:
        """عرض نتيجة Manual Sync."""
        self._set_sync_busy(False)
        QMessageBox.information(
            self,
            "Sync complete",
            (
                f"Downloaded: {downloaded}\n"
                f"Already present: {skipped}"
            ),
        )

    def _watch_sync_completed(
        self,
        checked: int,
        downloaded: int,
        skipped: int,
        failed: int,
    ) -> None:
        """عرض نتيجة Watch List وتحديث Last check في القائمة."""
        self._set_sync_busy(False)
        self._refresh_watch_list()
        self._log.append(
            "Watch List check complete. "
            f"Profiles: {checked}, new: {downloaded}, "
            f"existing: {skipped}, failed: {failed}."
        )

    def _sync_failed(self, message: str) -> None:
        """عرض خطأ Manual Sync مع إعادة الأزرار لوضعها الطبيعي."""
        self._set_sync_busy(False)
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
