@echo off
setlocal
py -m pip install -e .[dev]
pyinstaller --noconfirm --clean --windowed --name InstagramSync --paths src src\instagram_sync\__main__.py
echo.
echo Build complete: dist\InstagramSync\InstagramSync.exe
endlocal
