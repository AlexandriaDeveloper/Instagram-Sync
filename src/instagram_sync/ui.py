from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
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

from .database import MediaDatabase
from .instagram_client import InstagramClient
from .paths import database_path
from .sync_service import SyncService


class SyncWorker(QThread):
    status = Signal(str)
    completed = Signal(int, int)
    failed = Signal(str)

    def __init__(
        self,
        profile: str,
        destination: Path,
        username: str,
        include_posts: bool,
        include_reels: bool,
    ):
        super().__init__()
        self.profile = profile
        self.destination = destination
        self.username = username
        self.include_posts = include_posts
        self.include_reels = include_reels
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            db = MediaDatabase(database_path())
            client = InstagramClient(self.username)
            service = SyncService(db, client)
            result = service.sync(
                self.profile,
                self.destination,
                self.include_posts,
                self.include_reels,
                on_status=self.status.emit,
                should_cancel=lambda: self._cancelled,
            )
            self.completed.emit(result.downloaded, result.skipped)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instagram Sync")
        self.resize(720, 540)
        self.settings = QSettings("AlexandriaDeveloper", "InstagramSync")
        self.worker: SyncWorker | None = None
        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        title = QLabel("<h2>Instagram Sync</h2>")
        subtitle = QLabel("Download once, then sync only new media.")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        form = QFormLayout()
        self.profile = QLineEdit()
        self.profile.setPlaceholderText("target_profile")
        form.addRow("Profile:", self.profile)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Optional Instagram username")
        form.addRow("Login username:", self.username)

        destination_row = QHBoxLayout()
        self.destination = QLineEdit()
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse)
        destination_row.addWidget(self.destination)
        destination_row.addWidget(browse)
        form.addRow("Download folder:", destination_row)
        layout.addLayout(form)

        options = QHBoxLayout()
        self.posts = QCheckBox("Posts")
        self.posts.setChecked(True)
        self.reels = QCheckBox("Reels")
        self.reels.setChecked(True)
        options.addWidget(self.posts)
        options.addWidget(self.reels)
        options.addStretch()
        layout.addLayout(options)

        actions = QHBoxLayout()
        self.sync_btn = QPushButton("Sync Now")
        self.sync_btn.clicked.connect(self._start_sync)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel)
        actions.addWidget(self.sync_btn)
        actions.addWidget(self.cancel_btn)
        actions.addStretch()
        layout.addLayout(actions)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def _load_settings(self) -> None:
        self.username.setText(self.settings.value("username", "", str))
        default_downloads = str(Path.home() / "Downloads" / "InstagramSync")
        self.destination.setText(
            self.settings.value("destination", default_downloads, str)
        )

    def _save_settings(self) -> None:
        self.settings.setValue("username", self.username.text().strip())
        self.settings.setValue("destination", self.destination.text().strip())

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Choose download folder", self.destination.text()
        )
        if folder:
            self.destination.setText(folder)

    def _start_sync(self) -> None:
        profile = self.profile.text().strip().lstrip("@")
        destination = self.destination.text().strip()
        if not profile or not destination:
            QMessageBox.warning(self, "Missing information", "Enter a profile and folder.")
            return
        if not self.posts.isChecked() and not self.reels.isChecked():
            QMessageBox.warning(self, "Nothing selected", "Select Posts and/or Reels.")
            return

        self._save_settings()
        self.log.clear()
        self.sync_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress.setRange(0, 0)

        self.worker = SyncWorker(
            profile=profile,
            destination=Path(destination),
            username=self.username.text().strip(),
            include_posts=self.posts.isChecked(),
            include_reels=self.reels.isChecked(),
        )
        self.worker.status.connect(self.log.append)
        self.worker.completed.connect(self._completed)
        self.worker.failed.connect(self._failed)
        self.worker.start()

    def _cancel(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.log.append("Cancellation requested...")

    def _finish_ui(self) -> None:
        self.sync_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(1)

    def _completed(self, downloaded: int, skipped: int) -> None:
        self._finish_ui()
        QMessageBox.information(
            self,
            "Sync complete",
            f"Downloaded: {downloaded}\nAlready present: {skipped}",
        )

    def _failed(self, message: str) -> None:
        self._finish_ui()
        self.log.append(f"ERROR: {message}")
        QMessageBox.critical(self, "Sync failed", message)


def run_app() -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()
