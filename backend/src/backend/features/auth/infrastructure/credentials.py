from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.features.auth.domain.credentials import CredentialRepository, PasswordCredential
from backend.features.users.domain import Preferences
from backend.features.users.infrastructure.repository import preferences_adapter
from backend.platform.database.orm import PasswordCredentialRow, UserRow


class SqlCredentialRepository(CredentialRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def login_email(self, *, user_id: UUID) -> str | None:
        row = (
            await self._session.exec(
                select(PasswordCredentialRow).where(col(PasswordCredentialRow.user_id) == user_id)
            )
        ).one_or_none()
        return row.email if row else None

    async def find(self, *, email: str) -> PasswordCredential | None:
        # Authentication lookup precedes an owner identity; email is uniquely indexed.
        row = (
            await self._session.exec(
                select(PasswordCredentialRow).where(col(PasswordCredentialRow.email) == email)
            )
        ).one_or_none()
        return PasswordCredential(row.user_id, row.email, row.password_hash) if row else None

    async def register(self, *, credential: PasswordCredential) -> bool:
        try:
            async with self._session.begin_nested():
                self._session.add(
                    UserRow(
                        id=credential.user_id,
                        preferences=preferences_adapter.dump_python(Preferences(), mode="json"),
                    )
                )
                await self._session.flush()
                self._session.add(
                    PasswordCredentialRow(
                        user_id=credential.user_id,
                        email=credential.email,
                        password_hash=credential.password_hash,
                    )
                )
                await self._session.flush()
            return True
        except IntegrityError:
            if await self.find(email=credential.email) is not None:
                return False
            raise
