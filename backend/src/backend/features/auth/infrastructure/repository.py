from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.features.athletes.domain import Preferences
from backend.features.athletes.infrastructure.repository import preferences_adapter
from backend.features.auth.domain import (
    AuthRepository,
    ExternalIdentity,
    LoginAttempt,
    LoginSession,
)
from backend.platform.database.orm import AthleteRow, AttemptRow, IdentityRow, LoginRow


def aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class SqlAuthRepository(AuthRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_attempt(self, *, attempt: LoginAttempt) -> None:
        await self._session.execute(
            delete(AttemptRow).where(col(AttemptRow.expires_at) < datetime.now(UTC))
        )
        self._session.add(
            AttemptRow(
                state_hash=attempt.state_hash,
                verifier=attempt.verifier,
                nonce=attempt.nonce,
                expires_at=attempt.expires_at,
            )
        )
        await self._session.flush()

    async def consume_attempt(self, *, state_hash: str) -> LoginAttempt | None:
        row = (
            await self._session.exec(
                select(AttemptRow).where(col(AttemptRow.state_hash) == state_hash).with_for_update()
            )
        ).one_or_none()
        if row is None:
            return None
        # DELETE RETURNING makes consumption single-use on both PostgreSQL and SQLite.
        removed = await self._session.execute(
            delete(AttemptRow)
            .where(col(AttemptRow.state_hash) == state_hash)
            .returning(col(AttemptRow.state_hash))
        )
        if removed.scalar_one_or_none() is None:
            return None
        return LoginAttempt(
            state_hash=row.state_hash,
            verifier=row.verifier,
            nonce=row.nonce,
            expires_at=aware(row.expires_at),
        )

    async def resolve_identity(self, *, identity: ExternalIdentity, candidate_id: UUID) -> UUID:
        query = select(IdentityRow).where(
            col(IdentityRow.issuer) == identity.issuer, col(IdentityRow.subject) == identity.subject
        )
        existing = (await self._session.exec(query)).one_or_none()
        if existing:
            return existing.athlete_id
        try:
            async with self._session.begin_nested():
                self._session.add(
                    AthleteRow(
                        id=candidate_id,
                        preferences=preferences_adapter.dump_python(Preferences(), mode="json"),
                    )
                )
                await self._session.flush()
                self._session.add(
                    IdentityRow(
                        id=uuid4(),
                        athlete_id=candidate_id,
                        issuer=identity.issuer,
                        subject=identity.subject,
                    )
                )
                await self._session.flush()
            return candidate_id
        except IntegrityError:
            existing = (await self._session.exec(query)).one()
            return existing.athlete_id

    async def save_session(self, *, login_session: LoginSession) -> None:
        await self._session.execute(
            delete(LoginRow).where(col(LoginRow.expires_at) < datetime.now(UTC))
        )
        self._session.add(
            LoginRow(
                token_hash=login_session.token_hash,
                athlete_id=login_session.athlete_id,
                expires_at=login_session.expires_at,
            )
        )
        await self._session.flush()

    async def get_session(self, *, token_hash: str) -> LoginSession | None:
        row = await self._session.get(LoginRow, token_hash, populate_existing=True)
        return (
            LoginSession(
                token_hash=row.token_hash,
                athlete_id=row.athlete_id,
                expires_at=aware(row.expires_at),
            )
            if row
            else None
        )

    async def revoke(self, *, token_hash: str) -> None:
        await self._session.execute(delete(LoginRow).where(col(LoginRow.token_hash) == token_hash))
