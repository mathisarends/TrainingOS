from datetime import datetime
from typing import cast
from uuid import UUID

from pydantic import TypeAdapter
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.features.training_sessions.domain import (
    TrainingSession,
    TrainingSessionRepository,
    TrainingSessionSlot,
)
from backend.platform.database.orm import TrainingSessionRow

slots_adapter = TypeAdapter(tuple[TrainingSessionSlot, ...])


def to_domain(row: TrainingSessionRow) -> TrainingSession:
    data = row.payload
    return TrainingSession(
        id=row.id,
        user_id=row.user_id,
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


class SqlTrainingSessionRepository(TrainingSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, *, user_id: UUID) -> list[TrainingSession]:
        rows = await self._session.exec(
            select(TrainingSessionRow)
            .where(col(TrainingSessionRow.user_id) == user_id)
            .order_by(col(TrainingSessionRow.started_at), col(TrainingSessionRow.id))
        )
        return [to_domain(row) for row in rows]

    async def get(self, *, user_id: UUID, training_session_id: UUID) -> TrainingSession | None:
        row = (
            await self._session.exec(
                select(TrainingSessionRow).where(
                    col(TrainingSessionRow.user_id) == user_id,
                    col(TrainingSessionRow.id) == training_session_id,
                )
            )
        ).one_or_none()
        return to_domain(row) if row else None

    async def save(self, *, training_session: TrainingSession) -> None:
        payload = {
            "plan_title": training_session.plan_title,
            "day_name": training_session.day_name,
            "started_at": training_session.started_at.isoformat(),
            "ended_at": training_session.ended_at.isoformat()
            if training_session.ended_at
            else None,
            "rest_ends_at": training_session.rest_ends_at.isoformat()
            if training_session.rest_ends_at
            else None,
            "slots": slots_adapter.dump_python(training_session.slots, mode="json"),
        }
        row = TrainingSessionRow(
            id=training_session.id,
            user_id=training_session.user_id,
            plan_id=training_session.plan_id,
            day_id=training_session.day_id,
            week=training_session.week,
            started_at=training_session.started_at,
            ended_at=training_session.ended_at,
            payload=cast(dict[str, object], payload),
        )
        await self._session.merge(row)
        await self._session.flush()
