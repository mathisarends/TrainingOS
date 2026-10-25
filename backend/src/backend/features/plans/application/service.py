import copy
import hashlib
import secrets
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from backend.features.exercises.domain import Exercise, ExerciseRepository
from backend.features.plans.domain import (
    Plan,
    PlanRepository,
    PlanStatus,
    Prescription,
    Slot,
    TrainingDay,
)
from backend.features.training_sessions.domain import TrainingSessionRepository
from backend.shared import Conflict, InvalidInput, NotFound


@dataclass(frozen=True)
class DayDefinition:
    name: str
    weekday: int


@dataclass(frozen=True)
class NextTraining:
    plan_id: UUID
    day_id: UUID
    week: int
    scheduled_date: date
    running_training_session_id: UUID | None = None


class PlanService:
    def __init__(
        self,
        plan_repository: PlanRepository,
        exercise_repository: ExerciseRepository,
        training_session_repository: TrainingSessionRepository,
    ) -> None:
        self._plans, self._exercises, self._training_sessions = (
            plan_repository,
            exercise_repository,
            training_session_repository,
        )

    async def list(self, *, user_id: UUID) -> list[Plan]:
        return await self._plans.list(user_id=user_id)

    async def get(self, *, user_id: UUID, plan_id: UUID) -> Plan:
        plan = await self._plans.get(user_id=user_id, plan_id=plan_id)
        if plan is None:
            raise NotFound
        return plan

    async def create(
        self,
        *,
        user_id: UUID,
        title: str,
        start_date: date,
        weeks: int,
        days: tuple[DayDefinition, ...],
    ) -> Plan:
        training_days = tuple(
            TrainingDay(id=uuid4(), name=day.name, weekday=day.weekday) for day in days
        )
        plan = Plan(
            user_id=user_id,
            title=title,
            start_date=start_date,
            weeks=weeks,
            days=training_days,
        )
        await self._plans.save(plan=plan)
        return plan

    async def configure(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
        title: str,
        start_date: date,
        recommendations: bool,
    ) -> Plan:
        plan = await self.get(user_id=user_id, plan_id=plan_id)
        plan.configure(title=title, start_date=start_date, recommendations=recommendations)
        await self._plans.save(plan=plan)
        return plan

    async def set_status(self, *, user_id: UUID, plan_id: UUID, status: PlanStatus) -> Plan:
        plan = await self.get(user_id=user_id, plan_id=plan_id)
        if status == PlanStatus.ACTIVE:
            for current in await self._plans.list(user_id=user_id):
                if current.status == PlanStatus.ACTIVE and current.id != plan.id:
                    current.set_status(PlanStatus.ENDED)
                    await self._plans.save(plan=current)
        plan.set_status(status)
        await self._plans.save(plan=plan)
        return plan

    async def add_slot(
        self, *, user_id: UUID, plan_id: UUID, day_id: UUID, exercise_id: UUID, rest_seconds: int
    ) -> Plan:
        plan = await self.get(user_id=user_id, plan_id=plan_id)
        day = plan.day(day_id)
        exercise = await self._exercises.get(user_id=user_id, exercise_id=exercise_id)
        if exercise is None:
            raise NotFound
        if exercise.archived:
            raise Conflict("Archived exercises cannot be added to plans")
        slot = Slot(
            id=uuid4(),
            exercise_id=exercise.id,
            exercise_name=exercise.name,
            category=exercise.category,
            main=exercise.main,
            rest_seconds=rest_seconds,
        )
        plan.replace_day(replace(day, slots=day.slots + (slot,)))
        await self._plans.save(plan=plan)
        return plan

    async def reorder(
        self, *, user_id: UUID, plan_id: UUID, day_id: UUID, slot_ids: tuple[UUID, ...]
    ) -> Plan:
        plan = await self.get(user_id=user_id, plan_id=plan_id)
        day = plan.day(day_id)
        if len(slot_ids) != len(day.slots) or set(slot_ids) != {slot.id for slot in day.slots}:
            raise InvalidInput("Supply each existing slot exactly once")
        by_id = {slot.id: slot for slot in day.slots}
        plan.replace_day(replace(day, slots=tuple(by_id[id] for id in slot_ids)))
        await self._plans.save(plan=plan)
        return plan

    async def edit_day(
        self, *, user_id: UUID, plan_id: UUID, day_id: UUID, definition: DayDefinition
    ) -> Plan:
        plan = await self.get(user_id=user_id, plan_id=plan_id)
        day = plan.day(day_id)
        plan.replace_day(replace(day, name=definition.name, weekday=definition.weekday))
        await self._plans.save(plan=plan)
        return plan

    async def edit_slot(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
        day_id: UUID,
        slot_id: UUID,
        rest_seconds: int | None,
    ) -> Plan:
        plan = await self.get(user_id=user_id, plan_id=plan_id)
        day = plan.day(day_id)
        if not any(slot.id == slot_id for slot in day.slots):
            raise NotFound
        slots = (
            tuple(
                replace(slot, rest_seconds=rest_seconds) if slot.id == slot_id else slot
                for slot in day.slots
            )
            if rest_seconds is not None
            else tuple(slot for slot in day.slots if slot.id != slot_id)
        )
        plan.replace_day(replace(day, slots=slots))
        await self._plans.save(plan=plan)
        return plan

    async def prescribe(
        self, *, user_id: UUID, plan_id: UUID, slot_id: UUID, prescription: Prescription
    ) -> Plan:
        plan = await self.get(user_id=user_id, plan_id=plan_id)
        plan.prescribe(slot_id=slot_id, prescription=prescription)
        await self._plans.save(plan=plan)
        return plan

    async def copy_week(self, *, user_id: UUID, plan_id: UUID, week: int) -> Plan:
        plan = await self.get(user_id=user_id, plan_id=plan_id)
        plan.copy_week(week)
        await self._plans.save(plan=plan)
        return plan

    async def progression(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
        increment: Decimal,
        deload: bool,
        expected_revision: int | None = None,
    ) -> Plan:
        plan = copy.deepcopy(await self.get(user_id=user_id, plan_id=plan_id))
        if expected_revision is not None and expected_revision != plan.revision:
            raise Conflict("Plan changed; request a new progression preview")
        plan.progress(increment=increment, deload=deload)
        if expected_revision is not None:
            await self._plans.save(plan=plan)
        return plan

    async def duplicate(
        self, *, user_id: UUID, plan_id: UUID, title: str, start_date: date
    ) -> Plan:
        original = await self.get(user_id=user_id, plan_id=plan_id)
        plan = original.duplicate(user_id=user_id, title=title, start_date=start_date)
        await self._plans.save(plan=plan)
        return plan

    async def remove(self, *, user_id: UUID, plan_id: UUID) -> None:
        await self.get(user_id=user_id, plan_id=plan_id)
        await self._plans.delete(user_id=user_id, plan_id=plan_id)

    async def share(self, *, user_id: UUID, plan_id: UUID) -> str:
        plan = await self.get(user_id=user_id, plan_id=plan_id)
        token = secrets.token_urlsafe(32)
        await self._plans.share(
            user_id=user_id, token_hash=hashlib.sha256(token.encode()).hexdigest(), plan=plan
        )
        return token

    async def revoke_share(self, *, user_id: UUID, token: str) -> None:
        await self._plans.revoke(
            user_id=user_id, token_hash=hashlib.sha256(token.encode()).hexdigest()
        )

    async def import_template(
        self, *, user_id: UUID, token: str, title: str, start_date: date
    ) -> Plan:
        template = await self._plans.template(token_hash=hashlib.sha256(token.encode()).hexdigest())
        if template is None:
            raise NotFound
        plan = template.duplicate(user_id=user_id, title=title, start_date=start_date)
        catalog = await self._exercises.list(user_id=user_id)
        mapped: dict[UUID, Exercise] = {}
        for day in plan.days:
            slots: list[Slot] = []
            for slot in day.slots:
                if slot.exercise_id not in mapped:
                    exercise = next(
                        (
                            item
                            for item in catalog
                            if not item.archived
                            and item.name == slot.exercise_name
                            and item.category == slot.category
                            and item.main == slot.main
                        ),
                        None,
                    )
                    if exercise is None:
                        exercise = Exercise(
                            user_id=user_id,
                            name=slot.exercise_name,
                            category=slot.category,
                            main=slot.main,
                        )
                        await self._exercises.save(exercise=exercise)
                        catalog.append(exercise)
                    mapped[slot.exercise_id] = exercise
                slots.append(replace(slot, exercise_id=mapped[slot.exercise_id].id))
            plan.replace_day(replace(day, slots=tuple(slots)))
        await self._plans.save(plan=plan)
        return plan

    async def next_training(self, *, user_id: UUID) -> NextTraining | None:
        training_sessions = await self._training_sessions.list(user_id=user_id)
        running = next(
            (
                training_session
                for training_session in training_sessions
                if training_session.ended_at is None
            ),
            None,
        )
        if running:
            return NextTraining(
                plan_id=running.plan_id,
                day_id=running.day_id,
                week=running.week,
                scheduled_date=running.started_at.date(),
                running_training_session_id=running.id,
            )
        plans = await self._plans.list(user_id=user_id)
        active = next((plan for plan in plans if plan.status == PlanStatus.ACTIVE), None)
        if active is None:
            return None
        completed = {
            (training_session.day_id, training_session.week)
            for training_session in training_sessions
            if training_session.plan_id == active.id and training_session.ended_at is not None
        }
        # Week 1 is the seven-day interval beginning on start_date. Weekdays wrap within it.
        days = sorted(active.days, key=lambda day: (day.weekday - active.start_date.weekday()) % 7)
        for week in range(1, active.weeks + 1):
            for day in days:
                if (day.id, week) not in completed:
                    scheduled = active.start_date + timedelta(
                        days=(week - 1) * 7 + (day.weekday - active.start_date.weekday()) % 7
                    )
                    return NextTraining(
                        plan_id=active.id, day_id=day.id, week=week, scheduled_date=scheduled
                    )
        return None
