from typing import cast
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import delete
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.features.users.domain import Preferences, User, UserRepository
from backend.platform.database.orm import UserRow

preferences_adapter = TypeAdapter(Preferences)


class SqlUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, *, user_id: UUID, lock: bool = False) -> User | None:
        query = select(UserRow).where(col(UserRow.id) == user_id)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        row = (await self._session.exec(query)).one_or_none()
        return (
            User(id=row.id, preferences=preferences_adapter.validate_python(row.preferences))
            if row
            else None
        )

    async def save(self, *, user: User) -> None:
        row = UserRow(
            id=user.id,
            preferences=cast(
                dict[str, str | None],
                preferences_adapter.dump_python(user.preferences, mode="json"),
            ),
        )
        await self._session.merge(row)
        await self._session.flush()

    async def delete(self, *, user_id: UUID) -> None:
        await self._session.exec(delete(UserRow).where(col(UserRow.id) == user_id))
