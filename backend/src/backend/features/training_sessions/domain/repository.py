from abc import ABC, abstractmethod
from uuid import UUID

from .models import TrainingSession


class TrainingSessionRepository(ABC):
    @abstractmethod
    async def list(self, *, user_id: UUID) -> list[TrainingSession]: ...

    @abstractmethod
    async def get(self, *, user_id: UUID, training_session_id: UUID) -> TrainingSession | None: ...

    @abstractmethod
    async def save(self, *, training_session: TrainingSession) -> None: ...
