from typing import cast
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import delete
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.features.athletes.domain import Athlete, AthleteRepository, Preferences
from backend.platform.database.orm import AthleteRow

preferences_adapter = TypeAdapter(Preferences)


class SqlAthleteRepository(AthleteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, *, athlete_id: UUID, lock: bool = False) -> Athlete | None:
        query = select(AthleteRow).where(col(AthleteRow.id) == athlete_id)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        row = (await self._session.exec(query)).one_or_none()
        return (
            Athlete(id=row.id, preferences=preferences_adapter.validate_python(row.preferences))
            if row
            else None
        )

    async def save(self, *, athlete: Athlete) -> None:
        row = AthleteRow(
            id=athlete.id,
            preferences=cast(
                dict[str, str | None],
                preferences_adapter.dump_python(athlete.preferences, mode="json"),
            ),
        )
        await self._session.merge(row)
        await self._session.flush()

    async def delete(self, *, athlete_id: UUID) -> None:
        await self._session.exec(delete(AthleteRow).where(col(AthleteRow.id) == athlete_id))
