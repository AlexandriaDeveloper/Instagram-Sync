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


def session_dir() -> Path:
    """إرجاع مجلد Sessions المحلي خارج Repository."""
    path = app_data_dir() / "sessions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def session_path(username: str) -> Path:
    """إرجاع مسار Session لحساب Instagram بعد تنظيف الاسم."""
    safe_username = username.strip().lower()
    return session_dir() / f"{safe_username}.session"
