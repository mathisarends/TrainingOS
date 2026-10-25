from datetime import datetime
from typing import cast
from uuid import UUID

from pydantic import TypeAdapter
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.features.sessions.domain import Session, SessionRepository, SessionSlot
from backend.platform.database.orm import SessionRow

slots_adapter = TypeAdapter(tuple[SessionSlot, ...])


def to_domain(row: SessionRow) -> Session:
    data = row.payload
    return Session(
        id=row.id,
        athlete_id=row.athlete_id,
        plan_id=row.plan_id,
        day_id=row.day_id,
        week=row.week,
        plan_title=str(data["plan_title"]),
        day_name=str(data["day_name"]),
        slots=slots_adapter.validate_python(data["slots"]),
        started_at=datetime.fromisoformat(str(data["started_at"])),
        ended_at=datetime.fromisoformat(str(data["ended_at"])) if data["ended_at"] else None,
        rest_ends_at=datetime.fromisoformat(str(data["rest_ends_at"]))
        if data["rest_ends_at"]
        else None,
    )


class SqlSessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, *, athlete_id: UUID) -> list[Session]:
        rows = await self._session.exec(
            select(SessionRow)
            .where(col(SessionRow.athlete_id) == athlete_id)
            .order_by(col(SessionRow.started_at), col(SessionRow.id))
        )
        return [to_domain(row) for row in rows]

    async def get(self, *, athlete_id: UUID, session_id: UUID) -> Session | None:
        row = (
            await self._session.exec(
                select(SessionRow).where(
                    col(SessionRow.athlete_id) == athlete_id, col(SessionRow.id) == session_id
                )
            )
        ).one_or_none()
        return to_domain(row) if row else None

    async def save(self, *, session: Session) -> None:
        payload = {
            "plan_title": session.plan_title,
            "day_name": session.day_name,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "rest_ends_at": session.rest_ends_at.isoformat() if session.rest_ends_at else None,
            "slots": slots_adapter.dump_python(session.slots, mode="json"),
        }
        row = SessionRow(
            id=session.id,
            athlete_id=session.athlete_id,
            plan_id=session.plan_id,
            day_id=session.day_id,
            week=session.week,
            started_at=session.started_at,
            ended_at=session.ended_at,
            payload=cast(dict[str, object], payload),
        )
        await self._session.merge(row)
        await self._session.flush()
