from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from backend.features.bodyweight.domain import BodyweightRepository, WeighIn
from backend.shared import NotFound


class BodyweightService:
    def __init__(self, bodyweight_repository: BodyweightRepository) -> None:
        self._bodyweight = bodyweight_repository

    async def list(self, *, user_id: UUID) -> list[WeighIn]:
        return await self._bodyweight.list(user_id=user_id)

    async def record(self, *, user_id: UUID, date: date, weight_kg: Decimal) -> WeighIn:
        previous = await self._bodyweight.list(user_id=user_id)
        existing = next((item for item in previous if item.date == date), None)
        weigh_in = WeighIn(
            id=existing.id if existing else uuid4(),
            user_id=user_id,
            date=date,
            weight_kg=weight_kg,
        )
        await self._bodyweight.save(weigh_in=weigh_in)
        return weigh_in

    async def remove(self, *, user_id: UUID, weigh_in_id: UUID) -> None:
        previous = await self._bodyweight.list(user_id=user_id)
        if not any(item.id == weigh_in_id for item in previous):
            raise NotFound
        await self._bodyweight.delete(user_id=user_id, weigh_in_id=weigh_in_id)
