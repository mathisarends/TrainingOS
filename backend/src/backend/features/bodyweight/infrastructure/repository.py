from uuid import UUID

from sqlalchemy import delete
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.features.bodyweight.domain import BodyweightRepository, WeighIn
from backend.platform.database.orm import WeighInRow


class SqlBodyweightRepository(BodyweightRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, *, athlete_id: UUID) -> list[WeighIn]:
        rows = await self._session.exec(
            select(WeighInRow)
            .where(col(WeighInRow.athlete_id) == athlete_id)
            .order_by(col(WeighInRow.date))
        )
        return [
            WeighIn(id=row.id, athlete_id=row.athlete_id, date=row.date, weight_kg=row.weight_kg)
            for row in rows
        ]

    async def save(self, *, weigh_in: WeighIn) -> None:
        row = WeighInRow(
            id=weigh_in.id,
            athlete_id=weigh_in.athlete_id,
            date=weigh_in.date,
            weight_kg=weigh_in.weight_kg,
        )
        await self._session.merge(row)
        await self._session.flush()

    async def delete(self, *, athlete_id: UUID, weigh_in_id: UUID) -> None:
        await self._session.exec(
            delete(WeighInRow).where(
                col(WeighInRow.athlete_id) == athlete_id, col(WeighInRow.id) == weigh_in_id
            )
        )
