"""Errors that callers can handle without knowing the network adapter."""


class InstagramRateLimitError(RuntimeError):
    """Stop this sync after Instagram refuses further requests."""

    def __init__(self) -> None:
        super().__init__(
            "Instagram rate limit reached (HTTP 429). Synchronization stopped. "
            "Please wait before trying again manually; no automatic retry will be made."
        )
