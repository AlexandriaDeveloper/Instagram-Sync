"""اختبارات Watch List المحلية."""

from pathlib import Path

from instagram_sync.infrastructure.sqlite_watch_list import SQLiteWatchListRepository


def test_only_explicitly_added_profiles_are_watched(tmp_path: Path) -> None:
    """القائمة يجب ألا تعرف أي شيء عن Instagram Following."""
    repository = SQLiteWatchListRepository(
        tmp_path / "watch.sqlite3"
    )

    repository.add_profile("alpha")
    repository.add_profile("beta")
    repository.add_profile("alpha")

    assert [item.profile for item in repository.list_profiles()] == [
        "alpha",
        "beta",
    ]

    repository.remove_profile("alpha")

    assert [item.profile for item in repository.list_profiles()] == [
        "beta",
    ]
