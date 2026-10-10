"""اختبار Use Case الخاص بربط Session بدون متصفح حقيقي."""

import pytest

from instagram_sync.application.connect_session import ConnectBrowserSessionUseCase
from instagram_sync.domain.models import SessionInfo


class FakeImporter:
    """Importer وهمي لاختبار Application Layer فقط."""

    def import_session(self, browser: str) -> SessionInfo:
        return SessionInfo(
            username="example_user",
            browser=browser,
        )


def test_browser_name_is_normalized() -> None:
    """Use Case يحول اسم المتصفح لصيغة ثابتة."""
    use_case = ConnectBrowserSessionUseCase(
        FakeImporter()
    )

    info = use_case.execute(" Chrome ")

    assert info.username == "example_user"
    assert info.browser == "chrome"


def test_empty_browser_is_rejected() -> None:
    """لا يجوز تشغيل Import بدون اختيار متصفح."""
    use_case = ConnectBrowserSessionUseCase(
        FakeImporter()
    )

    with pytest.raises(
        ValueError,
        match="Choose a browser first",
    ):
        use_case.execute("   ")
