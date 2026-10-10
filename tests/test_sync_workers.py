"""Workers report rate limits as failure, and retain cancellation signals."""

from concurrent.futures import CancelledError
from unittest.mock import Mock

import pytest

from instagram_sync.application.errors import InstagramRateLimitError
from instagram_sync.domain.models import SyncRequest
from instagram_sync.presentation.workers import SyncWorker, WatchSyncWorker


@pytest.mark.parametrize("watch", [False, True])
@pytest.mark.parametrize("cancelled", [False, True])
def test_worker_stops_without_completion(monkeypatch, tmp_path, watch, cancelled):
    error = CancelledError("Synchronization cancelled.") if cancelled else InstagramRateLimitError()
    executor = Mock()
    executor.execute.side_effect = error
    factory = "build_watch_sync_use_case" if watch else "build_sync_use_case"
    monkeypatch.setattr(f"instagram_sync.presentation.workers.{factory}", lambda _: executor)
    worker = (
        WatchSyncWorker(tmp_path, "") if watch else SyncWorker(SyncRequest("example", tmp_path), "")
    )
    failures = []
    completions = []
    cancellations = []
    worker.failed.connect(failures.append)
    worker.completed.connect(lambda *args: completions.append(args))
    worker.cancelled.connect(lambda: cancellations.append(True))
    worker.cancel()
    worker.run()

    assert completions == []
    assert executor.execute.call_count == 1
    assert executor.execute.call_args.kwargs["should_cancel"]() is True
    assert failures == ([] if cancelled else [str(error)])
    assert cancellations == ([True] if cancelled else [])
