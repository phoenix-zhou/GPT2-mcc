"""Small, dependency-free safeguards for the local Flask reference demo."""

from __future__ import annotations

import secrets
import time
from collections import OrderedDict, deque
from collections.abc import MutableMapping
from threading import Lock
from typing import Any, Callable


CSRF_SESSION_KEY = "_csrf_token"


def get_or_create_csrf_token(session_data: MutableMapping[str, Any]) -> str:
    """Return a session-bound CSRF token without placing it in URLs."""
    token = session_data.get(CSRF_SESSION_KEY)
    if not isinstance(token, str) or len(token) < 32:
        token = secrets.token_urlsafe(32)
        session_data[CSRF_SESSION_KEY] = token
    return token


def is_valid_csrf_token(
    session_data: MutableMapping[str, Any], provided_token: str | None
) -> bool:
    """Compare a submitted form token with the signed-session value."""
    expected = session_data.get(CSRF_SESSION_KEY)
    return (
        isinstance(expected, str)
        and isinstance(provided_token, str)
        and bool(provided_token)
        and secrets.compare_digest(expected, provided_token)
    )


class InMemoryRateLimiter:
    """Bound request bursts while keeping the local demo dependency-free.

    This is a single-process safeguard, not a distributed production limiter.
    The LRU client cap prevents attacker-controlled identifiers from growing
    the bookkeeping structure without bound.
    """

    def __init__(
        self,
        *,
        max_requests: int = 10,
        window_seconds: int = 60,
        max_clients: int = 1000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if min(max_requests, window_seconds, max_clients) < 1:
            raise ValueError("rate-limit values must be positive integers")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self._clock = clock
        self._events: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = Lock()

    def allow(self, client_key: str) -> bool:
        now = self._clock()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events.setdefault(client_key, deque())
            while events and events[0] <= cutoff:
                events.popleft()
            self._events.move_to_end(client_key)
            if len(events) >= self.max_requests:
                return False
            events.append(now)
            while len(self._events) > self.max_clients:
                self._events.popitem(last=False)
            return True
