"""Exercise real Instaloader HTTP handling without contacting Instagram."""

from concurrent.futures import CancelledError
from unittest.mock import Mock

import instaloader
import pytest

from instagram_sync.application.errors import InstagramRateLimitError
from instagram_sync.infrastructure.instagram_source import (
    InstaloaderMediaSource,
    _CancellableRateController,
)


@pytest.mark.parametrize("stage", ["profile", "posts", "reels", "sidecar"])
def test_http_429_stops_at_first_request(monkeypatch, stage):
    source = InstaloaderMediaSource()
    context = source._loader.context
    monkeypatch.setattr(context, "do_sleep", Mock())
    monkeypatch.setattr(context._rate_controller, "wait_before_query", Mock())
    retry = Mock(side_effect=AssertionError("429 must not schedule a retry"))
    monkeypatch.setattr(context._rate_controller, "handle_429", retry)
    response = Mock(status_code=429, is_redirect=False, reason="Too Many Requests")
    response.json.return_value = {"status": "fail", "message": "Please wait"}
    get = Mock(return_value=response)
    monkeypatch.setattr(context._session, "get", get)

    def request():
        context.get_json("api/v1/users/web_profile_info/", {"username": "example"})

    def posts():
        request()
        yield  # pragma: no cover

    if stage != "profile":
        profile = Mock()
        profile.get_posts.return_value = posts()
        profile.get_reels.return_value = posts()
        if stage == "sidecar":
            post = Mock(typename="GraphSidecar", date_utc=None)
            post.get_sidecar_nodes.side_effect = request
            profile.get_posts.return_value = iter([post])
        monkeypatch.setattr(instaloader.Profile, "from_username", Mock(return_value=profile))

    with pytest.raises(InstagramRateLimitError, match="Please wait") as caught:
        list(source.iter_profile_media("example", include_posts=stage != "reels"))

    assert isinstance(caught.value.__cause__, instaloader.exceptions.ConnectionException)
    assert get.call_count == 1
    retry.assert_not_called()
    assert source._should_cancel() is False


@pytest.mark.parametrize("error", [
    instaloader.exceptions.ConnectionException("HTTP 500"),
    instaloader.exceptions.ProfileNotExistsException("missing"),
])
def test_other_errors_keep_their_identity(monkeypatch, error):
    source = InstaloaderMediaSource()
    monkeypatch.setattr(instaloader.Profile, "from_username", Mock(side_effect=error))
    with pytest.raises(type(error)) as caught:
        list(source.iter_profile_media("example"))
    assert caught.value is error


def test_cancel_wins_when_requested_during_429(monkeypatch):
    source = InstaloaderMediaSource()
    cancelled = False

    def request(*args):
        nonlocal cancelled
        cancelled = True
        raise instaloader.exceptions.TooManyRequestsException("429")

    monkeypatch.setattr(instaloader.Profile, "from_username", request)
    with pytest.raises(CancelledError):
        list(source.iter_profile_media("example", should_cancel=lambda: cancelled))
    assert source._should_cancel() is False


def test_rate_controller_sleep_still_cancels():
    source = InstaloaderMediaSource()
    controller = _CancellableRateController(source._loader.context, lambda: True)
    with pytest.raises(CancelledError):
        controller.sleep(600)


def test_cancel_before_scan_makes_no_request(monkeypatch):
    source = InstaloaderMediaSource()
    request = Mock()
    monkeypatch.setattr(instaloader.Profile, "from_username", request)
    with pytest.raises(CancelledError):
        list(source.iter_profile_media("example", should_cancel=lambda: True))
    request.assert_not_called()
