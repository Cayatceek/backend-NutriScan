from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


class RateLimitStorage(Protocol):
    def hit(self, *, namespace: str, key: str, limit: int, window_seconds: int) -> bool:
        """Return True when the request should be rate limited."""


class InMemoryRateLimitStorage:
    def __init__(self) -> None:
        self._buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, *, namespace: str, key: str, limit: int, window_seconds: int) -> bool:
        now = datetime.now(UTC).timestamp()
        bucket_key = (namespace, key)

        with self._lock:
            bucket = self._buckets[bucket_key]
            cutoff = now - window_seconds

            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                return True

            bucket.append(now)
            return False

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


rate_limit_storage: RateLimitStorage = InMemoryRateLimitStorage()


@dataclass(frozen=True)
class RateLimitPolicy:
    namespace: str
    limit: int
    window_seconds: int


def _client_key(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "anonymous"


def enforce_rate_limit(policy: RateLimitPolicy) -> Callable[[Request], None]:
    def dependency(request: Request) -> None:
        limited = rate_limit_storage.hit(
            namespace=policy.namespace,
            key=_client_key(request),
            limit=policy.limit,
            window_seconds=policy.window_seconds,
        )
        if limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

    return dependency


def auth_policy(namespace: str) -> RateLimitPolicy:
    settings = get_settings()
    return RateLimitPolicy(
        namespace=namespace,
        limit=settings.auth_rate_limit_count,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )


def off_policy(namespace: str) -> RateLimitPolicy:
    settings = get_settings()
    return RateLimitPolicy(
        namespace=namespace,
        limit=settings.off_rate_limit_count,
        window_seconds=settings.off_rate_limit_window_seconds,
    )
