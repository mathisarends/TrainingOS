from abc import ABC, abstractmethod
from uuid import UUID

from .models import User


class UserRepository(ABC):
    @abstractmethod
    async def get(self, *, user_id: UUID, lock: bool = False) -> User | None: ...

    @abstractmethod
    async def save(self, *, user: User) -> None: ...

    @abstractmethod
    async def delete(self, *, user_id: UUID) -> None: ...
