"""اختبارات Use Case الخاص بإدارة Session المحلية."""

from instagram_sync.application.manage_session import ManageSessionUseCase


class FakeSessionStore:
    """مخزن بسيط للاختبار بدون لمس نظام الملفات."""

    def __init__(self, existing: set[str] | None = None) -> None:
        self.existing = set(existing or set())
        self.removed: list[str] = []

    def exists(self, username: str) -> bool:
        return username in self.existing

    def remove(self, username: str) -> None:
        self.removed.append(username)
        self.existing.discard(username)


def test_is_connected_uses_store() -> None:
    store = FakeSessionStore({"alice"})
    use_case = ManageSessionUseCase(store)

    assert use_case.is_connected(" alice ")
    assert not use_case.is_connected("bob")
    assert not use_case.is_connected("")


def test_disconnect_delegates_to_store() -> None:
    store = FakeSessionStore({"alice"})
    use_case = ManageSessionUseCase(store)

    use_case.disconnect(" alice ")

    assert store.removed == ["alice"]
    assert not use_case.is_connected("alice")
