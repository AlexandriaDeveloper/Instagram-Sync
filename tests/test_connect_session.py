"""اختبار Use Case الخاص بحفظ Session بدون Instagram حقيقي."""

import pytest

from instagram_sync.application.connect_session import ConnectSessionUseCase
from instagram_sync.domain.models import SessionInfo


class FakeSessionWriter:
    """Writer وهمي يثبت أن Application Layer لا تعتمد على Instaloader."""

    def save_from_cookies(self, cookies):
        return SessionInfo(username="example_user")


def test_sessionid_is_required() -> None:
    """لا يجوز اعتماد Session قبل اكتمال تسجيل الدخول."""
    use_case = ConnectSessionUseCase(FakeSessionWriter())

    with pytest.raises(
        ValueError,
        match="login is not complete",
    ):
        use_case.execute({"csrftoken": "x"})


def test_verified_session_returns_username() -> None:
    """Session صالحة ترجع اسم الحساب المتصل."""
    use_case = ConnectSessionUseCase(FakeSessionWriter())

    info = use_case.execute(
        {"sessionid": "secret-test-value"}
    )

    assert info.username == "example_user"
