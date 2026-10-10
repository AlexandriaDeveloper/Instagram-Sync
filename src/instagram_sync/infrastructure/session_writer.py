"""حفظ Session لـInstaloader من Cookies متصفح التطبيق الخاص."""

from __future__ import annotations

from collections.abc import Mapping

import instaloader

from instagram_sync.domain.models import SessionInfo
from instagram_sync.paths import session_path


class InstaloaderSessionWriter:
    """التحقق من Cookies ثم حفظ Session بدون تخزين Password."""

    def save_from_cookies(
        self,
        cookies: Mapping[str, str],
    ) -> SessionInfo:
        """اختبار Session مع Instagram ثم حفظها محليًا."""
        loader = instaloader.Instaloader(quiet=True)

        # هذه Cookies تخص QWebEngine داخل التطبيق فقط، وليست Cookies متصفح المستخدم الأساسي.
        loader.context.update_cookies(dict(cookies))
        username = loader.test_login()

        if not username:
            raise RuntimeError(
                "Instagram session could not be verified. "
                "Complete login in the app window and try again."
            )

        loader.context.username = username
        loader.save_session_to_file(
            filename=str(session_path(username)),
        )

        return SessionInfo(username=username)
