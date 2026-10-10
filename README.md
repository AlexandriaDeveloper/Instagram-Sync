# Instagram Sync

Desktop app for synchronizing media from Instagram profiles you are allowed to access.

## Features

- Full sync on first run.
- Incremental sync afterwards: already-recorded media is skipped.
- Posts, Reels and carousel media.
- Local SQLite catalog keyed by shortcode + media index.
- Instagram session reuse through Instaloader session files.
- No Instagram password is stored in the repository or database.
- Windows EXE build script included.

## Requirements

- Python 3.11+
- Windows 10/11 recommended

## Run

```powershell
git clone https://github.com/AlexandriaDeveloper/Instagram-Sync.git
cd Instagram-Sync
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e .
python -m instagram_sync
```

## Login

For public profiles, login may not be required. For profiles your Instagram account can access,
enter your Instagram username in Settings and use **Load Session** after creating an Instaloader
session locally. The app never asks for your Instagram password.

## Build Windows EXE

```bat
build_windows.bat
```

Output: `dist\InstagramSync\InstagramSync.exe`.

## Data

App data is stored under the OS application-data directory. Downloads are saved to the folder
you select in the UI. SQLite stores synchronization metadata only.

## Safety

Use only for public profiles or content you are authorized to access. The app does not bypass
private-account restrictions, 2FA, or Instagram permissions.
