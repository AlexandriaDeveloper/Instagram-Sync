"""قواعد التحقق من اسم حساب Instagram في مكان مركزي."""


def normalize_profile_name(profile: str) -> str:
    """تنظيف اسم الحساب ومنع Path Traversal أو أحرف غير صالحة."""
    value = profile.strip().lstrip("@").lower()

    if not value:
        raise ValueError("Profile name is required.")

    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._")
    if len(value) > 30 or any(character not in allowed for character in value):
        raise ValueError("Invalid Instagram profile name.")

    return value
