from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PasswordCredential:
    user_id: UUID
    email: str
    password_hash: str


class CredentialRepository(ABC):
    @abstractmethod
    async def login_email(self, *, user_id: UUID) -> str | None: ...

    @abstractmethod
    async def find(self, *, email: str) -> PasswordCredential | None: ...

    @abstractmethod
    async def register(self, *, credential: PasswordCredential) -> bool: ...


class PasswordHasher(ABC):
    @abstractmethod
    async def hash(self, *, password: str) -> str: ...

    @abstractmethod
    async def verify(self, *, password: str, encoded: str | None) -> bool: ...


class CredentialThrottle(ABC):
    @abstractmethod
    async def check(self, *, email_key: str, client_key: str) -> None: ...
