import asyncio
import time
from collections import deque

from backend.features.auth.domain.credentials import CredentialThrottle
from backend.shared import RateLimited


class InMemoryCredentialThrottle(CredentialThrottle):
    """Bounded per-process protection; deployments can add a shared edge limit."""

    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    async def check(self, *, email_key: str, client_key: str) -> None:
        async with self._lock:
            now = time.monotonic()
            for key in list(self._attempts):
                bucket = self._attempts[key]
                while bucket and bucket[0] <= now - 300:
                    bucket.popleft()
                if not bucket:
                    del self._attempts[key]
            keys = [(f"email:{email_key}", 10), (f"client:{client_key}", 30)]
            if len(self._attempts) >= 20000 or any(
                len(self._attempts.get(key, ())) >= limit for key, limit in keys
            ):
                raise RateLimited
            for key, _ in keys:
                self._attempts.setdefault(key, deque()).append(now)
