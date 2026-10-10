@echo off
setlocal

REM تثبيت المشروع وأدوات التطوير قبل إنشاء نسخة Windows.
py -m pip install -e .[dev]

REM إنشاء تطبيق GUI بدون نافذة Console.
pyinstaller --noconfirm --clean --windowed ^
  --name InstagramSync ^
  --paths src ^
  src\instagram_sync\__main__.py

echo.
echo Build complete: dist\InstagramSync\InstagramSync.exe
endlocal
