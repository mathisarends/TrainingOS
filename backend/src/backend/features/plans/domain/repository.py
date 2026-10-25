from abc import ABC, abstractmethod
from uuid import UUID

from .models import Plan


class PlanRepository(ABC):
    @abstractmethod
    async def templates(self, *, athlete_id: UUID) -> list[Plan]: ...

    @abstractmethod
    async def list(self, *, athlete_id: UUID) -> list[Plan]: ...

    @abstractmethod
    async def get(self, *, athlete_id: UUID, plan_id: UUID) -> Plan | None: ...

    @abstractmethod
    async def save(self, *, plan: Plan) -> None: ...

    @abstractmethod
    async def delete(self, *, athlete_id: UUID, plan_id: UUID) -> None: ...

    @abstractmethod
    async def share(self, *, athlete_id: UUID, token_hash: str, plan: Plan) -> None: ...

    @abstractmethod
    async def template(self, *, token_hash: str) -> Plan | None: ...

    @abstractmethod
    async def revoke(self, *, athlete_id: UUID, token_hash: str) -> None: ...
