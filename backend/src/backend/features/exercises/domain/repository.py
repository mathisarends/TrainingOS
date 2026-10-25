from abc import ABC, abstractmethod
from uuid import UUID

from .models import Exercise


class ExerciseRepository(ABC):
    @abstractmethod
    async def list(self, *, user_id: UUID) -> list[Exercise]: ...

    @abstractmethod
    async def get(self, *, user_id: UUID, exercise_id: UUID) -> Exercise | None: ...

    @abstractmethod
    async def save(self, *, exercise: Exercise) -> None: ...

    @abstractmethod
    async def delete(self, *, user_id: UUID, exercise_id: UUID) -> None: ...
