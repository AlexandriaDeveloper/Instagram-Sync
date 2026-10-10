"""مسارات البيانات المحلية الخاصة بالتطبيق."""

from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "InstagramSync"
APP_AUTHOR = "AlexandriaDeveloper"


def app_data_dir() -> Path:
    """إرجاع مجلد بيانات التطبيق وإنشاؤه عند الحاجة."""
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    """إرجاع مسار قاعدة SQLite المحلية."""
    return app_data_dir() / "instagram_sync.sqlite3"
