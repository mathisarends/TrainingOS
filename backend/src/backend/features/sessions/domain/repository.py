from abc import ABC, abstractmethod
from uuid import UUID

from .models import Session


class SessionRepository(ABC):
    @abstractmethod
    async def list(self, *, athlete_id: UUID) -> list[Session]: ...

    @abstractmethod
    async def get(self, *, athlete_id: UUID, session_id: UUID) -> Session | None: ...

    @abstractmethod
    async def save(self, *, session: Session) -> None: ...
