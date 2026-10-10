"""Downloader بسيط وآمن نسبيًا للملفات Binary."""

from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen


class UrlLibBinaryDownloader:
    """تنزيل إلى ملف .part ثم الاستبدال الذري بعد اكتمال التنزيل."""

    _USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/126 Safari/537.36"
    )

    def download(self, url: str, path: Path) -> None:
        """تنزيل الملف مع تنظيف الملف المؤقت عند أي خطأ."""
        temp_path = path.with_suffix(path.suffix + ".part")
        request = Request(url, headers={"User-Agent": self._USER_AGENT})

        try:
            with urlopen(request, timeout=60) as response, temp_path.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)

            # لا يظهر الملف النهائي إلا بعد اكتمال كل البيانات.
            temp_path.replace(path)

        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
