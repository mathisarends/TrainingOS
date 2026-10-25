from abc import ABC, abstractmethod
from uuid import UUID

from .models import WeighIn


class BodyweightRepository(ABC):
    @abstractmethod
    async def list(self, *, athlete_id: UUID) -> list[WeighIn]: ...

    @abstractmethod
    async def save(self, *, weigh_in: WeighIn) -> None: ...

    @abstractmethod
    async def delete(self, *, athlete_id: UUID, weigh_in_id: UUID) -> None: ...
