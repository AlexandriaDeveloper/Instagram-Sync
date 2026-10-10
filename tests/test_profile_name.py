"""اختبارات تطبيع اسم حساب Instagram."""

import pytest

from instagram_sync.application.profile_name import normalize_profile_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Target.Profile", "target.profile"),
        ("@Target_Profile", "target_profile"),
        ("https://www.instagram.com/Target.Profile/", "target.profile"),
        ("https://instagram.com/Target_Profile", "target_profile"),
        ("instagram.com/Target.Profile/", "target.profile"),
        ("www.instagram.com/Target_Profile", "target_profile"),
    ],
)
def test_normalize_profile_name_accepts_supported_forms(
    raw: str,
    expected: str,
) -> None:
    assert normalize_profile_name(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "https://evilinstagram.com/target",
        "http://instagram.com/target",
        "https://www.instagram.com/p/ABC123/",
        "bad/name",
        "bad name",
        "name!",
    ],
)
def test_normalize_profile_name_rejects_invalid_values(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_profile_name(raw)
