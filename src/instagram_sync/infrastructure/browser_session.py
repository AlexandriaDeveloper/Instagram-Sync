"""استيراد Instagram Session من Cookies المتصفح المحلي.

لا يتم طلب Password. القيم الحساسة تظل على جهاز المستخدم.
"""

from __future__ import annotations

from collections.abc import Callable
from http.cookiejar import CookieJar
from typing import ClassVar

import browser_cookie3
import instaloader

from instagram_sync.domain.models import SessionInfo
from instagram_sync.paths import session_path


class InstaloaderBrowserSessionImporter:
    """استخدام browser_cookie3 ثم حفظ Session بصيغة Instaloader."""

    _BROWSERS: ClassVar[dict[str, Callable[..., CookieJar]]] = {
        "brave": browser_cookie3.brave,
        "chrome": browser_cookie3.chrome,
        "chromium": browser_cookie3.chromium,
        "edge": browser_cookie3.edge,
        "firefox": browser_cookie3.firefox,
        "librewolf": browser_cookie3.librewolf,
        "opera": browser_cookie3.opera,
        "opera_gx": browser_cookie3.opera_gx,
        "vivaldi": browser_cookie3.vivaldi,
    }

    def import_session(self, browser: str) -> SessionInfo:
        """استيراد Cookies الخاصة بـInstagram والتحقق منها ثم حفظ Session."""
        normalized = browser.strip().lower()
        browser_reader = self._BROWSERS.get(normalized)

        if browser_reader is None:
            raise ValueError(f"Unsupported browser: {browser}")

        cookie_jar = browser_reader()
        instagram_cookies = {
            cookie.name: cookie.value
            for cookie in cookie_jar
            if "instagram" in cookie.domain.lower()
        }

        if not instagram_cookies:
            raise RuntimeError(
                "No Instagram cookies were found. "
                "Log in to Instagram in the selected browser first."
            )

        loader = instaloader.Instaloader(quiet=True)
        loader.context.update_cookies(instagram_cookies)
        username = loader.test_login()

        if not username:
            raise RuntimeError(
                "Instagram session could not be verified. "
                "Re-login in the browser and try again."
            )

        loader.context.username = username
        loader.save_session_to_file(filename=str(session_path(username)))

        return SessionInfo(
            username=username,
            browser=normalized,
        )
