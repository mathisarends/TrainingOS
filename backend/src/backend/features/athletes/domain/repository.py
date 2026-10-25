from abc import ABC, abstractmethod
from uuid import UUID

from .models import Athlete


class AthleteRepository(ABC):
    @abstractmethod
    async def get(self, *, athlete_id: UUID, lock: bool = False) -> Athlete | None: ...

    @abstractmethod
    async def save(self, *, athlete: Athlete) -> None: ...

    @abstractmethod
    async def delete(self, *, athlete_id: UUID) -> None: ...
