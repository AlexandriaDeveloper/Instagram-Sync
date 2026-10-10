"""Download errors leave no partial file and are never retried."""

from unittest.mock import Mock
from urllib.error import HTTPError

import pytest

from instagram_sync.application.errors import InstagramRateLimitError
from instagram_sync.infrastructure.http_downloader import UrlLibBinaryDownloader


@pytest.mark.parametrize("code", [429, 403, 500])
@pytest.mark.parametrize("during_read", [False, True])
def test_http_failure_preserves_existing_file(monkeypatch, tmp_path, code, during_read):
    path = tmp_path / "existing.jpg"
    path.write_bytes(b"previous complete download")
    error = HTTPError("https://example.invalid/media", code, "HTTP failure", {}, None)
    if during_read:
        response = Mock()
        response.read.side_effect = [b"partial content", error]
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        request = Mock(return_value=response)
    else:
        request = Mock(side_effect=error)
    monkeypatch.setattr("instagram_sync.infrastructure.http_downloader.urlopen", request)

    expected = InstagramRateLimitError if code == 429 else HTTPError
    with pytest.raises(expected):
        UrlLibBinaryDownloader().download("https://example.invalid/media", path)

    assert request.call_count == 1
    assert path.read_bytes() == b"previous complete download"
    assert not path.with_suffix(".jpg.part").exists()
