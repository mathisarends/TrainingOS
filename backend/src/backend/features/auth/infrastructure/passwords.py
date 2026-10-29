import secrets

import anyio
from argon2 import PasswordHasher as Argon2
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type

from backend.features.auth.domain.credentials import PasswordHasher


class ArgonPasswords(PasswordHasher):
    def __init__(self) -> None:
        self._hasher = Argon2(time_cost=2, memory_cost=19456, parallelism=1, type=Type.ID)
        self._dummy = self._hasher.hash(secrets.token_urlsafe(32))
        self._capacity = anyio.CapacityLimiter(2)

    async def hash(self, *, password: str) -> str:
        return await anyio.to_thread.run_sync(self._hasher.hash, password, limiter=self._capacity)

    async def verify(self, *, password: str, encoded: str | None) -> bool:
        def check() -> bool:
            try:
                valid = self._hasher.verify(encoded or self._dummy, password)
                return valid and encoded is not None
            except (VerificationError, InvalidHashError):
                return False

        return await anyio.to_thread.run_sync(check, limiter=self._capacity)
