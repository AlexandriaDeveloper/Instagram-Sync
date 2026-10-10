"""قواعد التحقق من اسم حساب Instagram في مكان مركزي."""

from urllib.parse import urlparse


def normalize_profile_name(profile: str) -> str:
    """تنظيف اسم الحساب أو رابط الحساب مع منع Path Traversal والقيم غير الصالحة."""
    value = profile.strip()

    if not value:
        raise ValueError("Profile name is required.")

    if value.startswith("@"):
        value = value[1:]
    else:
        lowered = value.lower()
        if lowered.startswith("instagram.com/") or lowered.startswith(
            "www.instagram.com/"
        ):
            value = f"https://{value}"

        if "://" in value:
            parsed = urlparse(value)
            host = (parsed.hostname or "").lower().rstrip(".")
            is_instagram_host = (
                host == "instagram.com" or host.endswith(".instagram.com")
            )
            path_parts = [
                part for part in parsed.path.split("/") if part
            ]

            if (
                parsed.scheme.lower() != "https"
                or not is_instagram_host
                or len(path_parts) != 1
            ):
                raise ValueError("Invalid Instagram profile name.")

            value = path_parts[0]

    value = value.strip().lower()

    if not value:
        raise ValueError("Profile name is required.")

    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._")
    if len(value) > 30 or any(character not in allowed for character in value):
        raise ValueError("Invalid Instagram profile name.")

    return value
