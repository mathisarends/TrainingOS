from datetime import date
from typing import cast
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import delete
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.features.plans.domain import Plan, PlanRepository, PlanStatus, TrainingDay
from backend.platform.database.orm import PlanRow, TemplateRow

days_adapter = TypeAdapter(tuple[TrainingDay, ...])


def to_payload(plan: Plan) -> dict[str, object]:
    return {
        "id": str(plan.id),
        "athlete_id": str(plan.athlete_id),
        "title": plan.title,
        "start_date": plan.start_date.isoformat(),
        "weeks": plan.weeks,
        "days": days_adapter.dump_python(plan.days, mode="json"),
        "status": plan.status.value,
        "recommendations": plan.recommendations,
        "revision": plan.revision,
    }


def from_payload(data: dict[str, object]) -> Plan:
    return Plan(
        id=UUID(str(data["id"])),
        athlete_id=UUID(str(data["athlete_id"])),
        title=str(data["title"]),
        start_date=date.fromisoformat(str(data["start_date"])),
        weeks=cast(int, data["weeks"]),
        days=days_adapter.validate_python(data["days"]),
        status=PlanStatus(str(data["status"])),
        recommendations=cast(bool, data["recommendations"]),
        revision=cast(int, data["revision"]),
    )


class SqlPlanRepository(PlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, *, athlete_id: UUID) -> list[Plan]:
        rows = await self._session.exec(
            select(PlanRow).where(col(PlanRow.athlete_id) == athlete_id).order_by(col(PlanRow.id))
        )
        return [from_payload(row.payload) for row in rows]

    async def get(self, *, athlete_id: UUID, plan_id: UUID) -> Plan | None:
        row = (
            await self._session.exec(
                select(PlanRow).where(
                    col(PlanRow.athlete_id) == athlete_id, col(PlanRow.id) == plan_id
                )
            )
        ).one_or_none()
        return from_payload(row.payload) if row else None

    async def save(self, *, plan: Plan) -> None:
        row = PlanRow(
            id=plan.id, athlete_id=plan.athlete_id, status=plan.status, payload=to_payload(plan)
        )
        await self._session.merge(row)
        await self._session.flush()

    async def delete(self, *, athlete_id: UUID, plan_id: UUID) -> None:
        await self._session.exec(
            delete(PlanRow).where(col(PlanRow.athlete_id) == athlete_id, col(PlanRow.id) == plan_id)
        )

    async def share(self, *, athlete_id: UUID, token_hash: str, plan: Plan) -> None:
        self._session.add(
            TemplateRow(token_hash=token_hash, athlete_id=athlete_id, payload=to_payload(plan))
        )
        await self._session.flush()

    async def template(self, *, token_hash: str) -> Plan | None:
        row = await self._session.get(TemplateRow, token_hash)
        return from_payload(row.payload) if row else None

    async def revoke(self, *, athlete_id: UUID, token_hash: str) -> None:
        await self._session.exec(
            delete(TemplateRow).where(
                col(TemplateRow.athlete_id) == athlete_id, col(TemplateRow.token_hash) == token_hash
            )
        )
