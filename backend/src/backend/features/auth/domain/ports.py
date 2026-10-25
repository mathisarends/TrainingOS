from abc import ABC, abstractmethod
from uuid import UUID

from .models import ExternalIdentity, LoginAttempt, LoginSession


class IdentityProvider(ABC):
    @abstractmethod
    def authorize_url(self, *, state: str, verifier: str, nonce: str) -> str: ...

    @abstractmethod
    async def exchange(self, *, code: str, verifier: str, nonce: str) -> ExternalIdentity: ...


class AuthRepository(ABC):
    @abstractmethod
    async def save_attempt(self, *, attempt: LoginAttempt) -> None: ...

    @abstractmethod
    async def consume_attempt(self, *, state_hash: str) -> LoginAttempt | None: ...

    @abstractmethod
    async def resolve_identity(self, *, identity: ExternalIdentity, candidate_id: UUID) -> UUID: ...

    @abstractmethod
    async def save_session(self, *, login_session: LoginSession) -> None: ...

    @abstractmethod
    async def get_session(self, *, token_hash: str) -> LoginSession | None: ...

    @abstractmethod
    async def revoke(self, *, token_hash: str) -> None: ...
