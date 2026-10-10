"""النافذة الرئيسية للتطبيق.

الواجهة تجمع Input وتعرض Progress فقط؛ منطق المزامنة موجود في Application Layer.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QThread, QTimer, QUrl, Signal
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
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
from instagram_sync.paths import session_path


class InstagramLoginDialog(QDialog):
    """متصفح خاص بالتطبيق لتسجيل الدخول مباشرة في Instagram.

    التطبيق لا يقرأ Password ولا Cookies من متصفح المستخدم الأساسي.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """إنشاء Browser Profile مؤقت وتجميع Cookies الخاصة بـInstagram فقط."""
        super().__init__(parent)
        self.setWindowTitle("Login to Instagram")
        self.resize(980, 760)

        self._cookies: dict[str, str] = {}

        # Profile بدون اسم يكون Off-the-Record؛ لا يحفظ Cookies المتصفح بشكل دائم.
        self._web_profile = QWebEngineProfile(self)
        self._web_page = QWebEnginePage(self._web_profile, self)
        self._web_view = QWebEngineView(self)
        self._web_view.setPage(self._web_page)

        cookie_store = self._web_profile.cookieStore()
        cookie_store.cookieAdded.connect(self._on_cookie_added)

        self._status = QLabel(
            "Sign in to Instagram here. When login is complete, the button below will activate."
        )
        self._accept_button = QPushButton("Use This Instagram Session")
        self._accept_button.setEnabled(False)
        self._accept_button.clicked.connect(self.accept)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self._accept_button)
        buttons.addWidget(cancel_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._status)
        layout.addWidget(self._web_view, 1)
        layout.addLayout(buttons)

        self._web_view.setUrl(
            QUrl("https://www.instagram.com/accounts/login/")
        )

    def _on_cookie_added(self, cookie) -> None:
        """حفظ Cookies التابعة لـInstagram داخل الذاكرة فقط."""
        domain = cookie.domain().lower()
        if "instagram.com" not in domain:
            return

        name = bytes(cookie.name()).decode("utf-8", errors="ignore")
        value = bytes(cookie.value()).decode("utf-8", errors="ignore")
        self._cookies[name] = value

        # sessionid يظهر بعد نجاح تسجيل الدخول الفعلي بما فيه 2FA إن وجد.
        if name == "sessionid" and value:
            self._accept_button.setEnabled(True)
            self._status.setText(
                "Instagram login detected. You can now use this session."
            )

    def instagram_cookies(self) -> dict[str, str]:
        """إرجاع نسخة من Cookies المجمعة للـUse Case بعد قبول المستخدم."""
        return dict(self._cookies)


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


class MainWindow(QMainWindow):
    """واجهة التطبيق الرئيسية."""

    def __init__(self) -> None:
        """إنشاء الواجهة وتحميل الإعدادات ثم جدولة Check واحد عند الفتح."""
        super().__init__()
        self.setWindowTitle("Instagram Sync")
        self.resize(860, 720)

        self._settings = QSettings(
            "AlexandriaDeveloper",
            "InstagramSync",
        )
        self._sync_worker: SyncWorker | None = None
        self._watch_worker: WatchSyncWorker | None = None

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
                "Public profiles work without login. Private profiles work only when "
                "the connected Instagram account already has permission to view them."
            )
        )

        account_group = QGroupBox("Instagram account")
        account_layout = QHBoxLayout(account_group)

        self._account_label = QLabel("Not connected")
        self._login_button = QPushButton("Login to Instagram")
        self._login_button.clicked.connect(self._login_to_instagram)
        self._disconnect_button = QPushButton("Disconnect")
        self._disconnect_button.clicked.connect(self._disconnect_session)

        account_layout.addWidget(self._account_label)
        account_layout.addStretch()
        account_layout.addWidget(self._login_button)
        account_layout.addWidget(self._disconnect_button)
        layout.addWidget(account_group)

        form = QFormLayout()

        self._profile = QLineEdit()
        self._profile.setPlaceholderText("target_profile")
        form.addRow("Target profile:", self._profile)

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
        """استرجاع اسم الحساب المتصل ومجلد التنزيل فقط."""
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

        username = self._settings.value("username", "", str).strip()
        if username and session_path(username).exists():
            self._account_label.setText(f"Connected as @{username}")
        else:
            self._settings.remove("username")
            self._account_label.setText("Not connected")

        self._disconnect_button.setEnabled(bool(self._connected_username()))

    def _connected_username(self) -> str:
        """إرجاع اسم الحساب لو Session موجودة فعليًا."""
        username = self._settings.value("username", "", str).strip()
        if username and session_path(username).exists():
            return username
        return ""

    def _save_destination(self) -> None:
        """حفظ مجلد التنزيل فقط."""
        self._settings.setValue(
            "destination",
            self._destination.text().strip(),
        )

    def _login_to_instagram(self) -> None:
        """فتح صفحة Instagram في Browser خاص بالتطبيق وحفظ Session بعد نجاح الدخول."""
        dialog = InstagramLoginDialog(self)

        if dialog.exec() != QDialog.Accepted:
            return

        try:
            self._login_button.setEnabled(False)
            self._log.append("Verifying Instagram session...")

            use_case = build_connect_session_use_case()
            info = use_case.execute(dialog.instagram_cookies())

            self._settings.setValue("username", info.username)
            self._account_label.setText(
                f"Connected as @{info.username}"
            )
            self._disconnect_button.setEnabled(True)
            self._log.append(
                f"Instagram session saved for @{info.username}."
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(
                self,
                "Instagram login failed",
                str(exc),
            )
        finally:
            self._login_button.setEnabled(True)

    def _disconnect_session(self) -> None:
        """حذف Session المحلية للحساب المتصل بدون لمس حساب Instagram نفسه."""
        username = self._connected_username()
        if username:
            session_path(username).unlink(missing_ok=True)

        self._settings.remove("username")
        self._account_label.setText("Not connected")
        self._disconnect_button.setEnabled(False)
        self._log.append("Local Instagram session removed.")

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

        self._save_destination()
        self._set_sync_busy(True)

        request = SyncRequest(
            profile=profile,
            destination=Path(destination),
            include_posts=self._posts.isChecked(),
            include_reels=self._reels.isChecked(),
        )

        self._sync_worker = SyncWorker(
            request=request,
            username=self._connected_username(),
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

        self._save_destination()
        self._set_sync_busy(True)

        self._watch_worker = WatchSyncWorker(
            destination=Path(destination),
            username=self._connected_username(),
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
