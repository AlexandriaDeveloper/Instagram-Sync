from pathlib import Path
from platformdirs import user_data_dir

APP_NAME = "InstagramSync"
APP_AUTHOR = "AlexandriaDeveloper"

def app_data_dir() -> Path:
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path

def database_path() -> Path:
    return app_data_dir() / "instagram_sync.sqlite3"

def session_dir() -> Path:
    path = app_data_dir() / "sessions"
    path.mkdir(parents=True, exist_ok=True)
    return path
