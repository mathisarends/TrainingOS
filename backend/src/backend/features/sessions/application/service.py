from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from backend.features.athletes.domain import Preferences
from backend.features.plans.domain import PlanRepository, PlanStatus
from backend.features.sessions.domain import Session, SessionRepository, SessionSlot, WorkSet
from backend.features.training.domain import backoff, e1rm
from backend.shared import Conflict, InvalidInput, NotFound


@dataclass(frozen=True)
class SlotGuidance:
    recommended_weight_kg: Decimal | None
    backoff_weight_kg: Decimal | None
    last_sets: tuple[WorkSet, ...]
    last_performed_at: datetime | None


@dataclass(frozen=True)
class SetFeedback:
    session: Session
    work_set: WorkSet
    e1rm_kg: Decimal
    backoff_weight_kg: Decimal
    new_personal_record: bool


class SessionService:
    def __init__(
        self, session_repository: SessionRepository, plan_repository: PlanRepository
    ) -> None:
        self._sessions, self._plans = session_repository, plan_repository

    async def get(self, *, athlete_id: UUID, session_id: UUID) -> Session:
        session = await self._sessions.get(athlete_id=athlete_id, session_id=session_id)
        if session is None:
            raise NotFound
        return session

    async def list(self, *, athlete_id: UUID, offset: int, limit: int) -> list[Session]:
        sessions = await self._sessions.list(athlete_id=athlete_id)
        return list(reversed(sessions))[offset : offset + limit]

    async def start(self, *, athlete_id: UUID, plan_id: UUID, day_id: UUID, week: int) -> Session:
        plan = await self._plans.get(athlete_id=athlete_id, plan_id=plan_id)
        if plan is None:
            raise NotFound
        if plan.status in (PlanStatus.ARCHIVED, PlanStatus.ENDED):
            raise Conflict("This plan has ended or is archived")
        if not 1 <= week <= plan.weeks:
            raise InvalidInput("Week exceeds plan length")
        day = plan.day(day_id)
        if not day.slots:
            raise Conflict("The training day has no exercise slots")
        sessions = await self._sessions.list(athlete_id=athlete_id)
        if any(item.ended_at is None for item in sessions):
            raise Conflict("Finish the running session before starting another")
        if any(
            item.plan_id == plan_id and item.day_id == day_id and item.week == week
            for item in sessions
        ):
            raise Conflict("A session already exists for this training day and week")
        slots = tuple(
            SessionSlot(
                id=slot.id,
                exercise_id=slot.exercise_id,
                exercise_name=slot.exercise_name,
                category=slot.category,
                main=slot.main,
                rest_seconds=slot.rest_seconds,
                prescription=slot.prescription(week),
            )
            for slot in day.slots
        )
        session = Session(
            athlete_id=athlete_id,
            plan_id=plan.id,
            plan_title=plan.title,
            day_id=day.id,
            day_name=day.name,
            week=week,
            slots=slots,
        )
        await self._sessions.save(session=session)
        return session

    async def record(
        self,
        *,
        athlete_id: UUID,
        session_id: UUID,
        slot_id: UUID,
        weight_kg: Decimal,
        reps: int,
        rpe: Decimal,
        preferences: Preferences,
        set_id: UUID | None = None,
    ) -> SetFeedback:
        session = await self.get(athlete_id=athlete_id, session_id=session_id)
        slot = session.slot(slot_id)
        all_sessions = await self._sessions.list(athlete_id=athlete_id)
        historical = [
            e1rm(weight_kg=item.weight_kg, reps=item.reps, rpe=item.rpe, preferences=preferences)
            for previous in all_sessions
            for old_slot in previous.slots
            if old_slot.exercise_id == slot.exercise_id
            for item in old_slot.sets
            if item.id != set_id
        ]
        work_set = session.record(
            slot_id=slot_id,
            weight_kg=weight_kg,
            reps=reps,
            rpe=rpe,
            now=datetime.now(UTC),
            set_id=set_id,
        )
        maximum = e1rm(weight_kg=weight_kg, reps=reps, rpe=rpe, preferences=preferences)
        top = max(
            e1rm(weight_kg=item.weight_kg, reps=item.reps, rpe=item.rpe, preferences=preferences)
            for item in session.slot(slot_id).sets
        )
        backoff_weight = backoff(
            maximum_kg=top,
            reps=slot.prescription.reps,
            rpe=slot.prescription.target_rpe,
            preferences=preferences,
        )
        await self._sessions.save(session=session)
        return SetFeedback(
            session=session,
            work_set=work_set,
            e1rm_kg=maximum,
            backoff_weight_kg=backoff_weight,
            new_personal_record=slot.main and maximum > max(historical, default=Decimal(0)),
        )

    async def guidance(
        self, *, athlete_id: UUID, session_id: UUID, slot_id: UUID, preferences: Preferences
    ) -> SlotGuidance:
        session = await self.get(athlete_id=athlete_id, session_id=session_id)
        slot = session.slot(slot_id)
        history = await self._sessions.list(athlete_id=athlete_id)
        previous = [
            (item, old_slot)
            for item in reversed(history)
            if item.id != session.id and item.started_at <= session.started_at
            for old_slot in item.slots
            if old_slot.id == slot.id and old_slot.sets
        ]
        matching = next(
            (
                (item, old_slot)
                for item, old_slot in previous
                if old_slot.prescription.reps == slot.prescription.reps
            ),
            None,
        )
        plan = await self._plans.get(athlete_id=athlete_id, plan_id=session.plan_id)
        recommended = None
        if matching and (plan is None or plan.recommendations):
            top = max(
                e1rm(
                    weight_kg=item.weight_kg, reps=item.reps, rpe=item.rpe, preferences=preferences
                )
                for item in matching[1].sets
            )
            recommended = backoff(
                maximum_kg=top,
                reps=slot.prescription.reps,
                rpe=slot.prescription.target_rpe,
                preferences=preferences,
            )
        backoff_weight = None
        if slot.sets:
            top = max(
                e1rm(
                    weight_kg=item.weight_kg, reps=item.reps, rpe=item.rpe, preferences=preferences
                )
                for item in slot.sets
            )
            backoff_weight = backoff(
                maximum_kg=top,
                reps=slot.prescription.reps,
                rpe=slot.prescription.target_rpe,
                preferences=preferences,
            )
        return SlotGuidance(
            recommended_weight_kg=recommended,
            backoff_weight_kg=backoff_weight,
            last_sets=previous[0][1].sets if previous else (),
            last_performed_at=previous[0][0].started_at if previous else None,
        )

    async def remove_set(
        self, *, athlete_id: UUID, session_id: UUID, slot_id: UUID, set_id: UUID
    ) -> Session:
        session = await self.get(athlete_id=athlete_id, session_id=session_id)
        session.remove_set(slot_id=slot_id, set_id=set_id)
        await self._sessions.save(session=session)
        return session

    async def skip(
        self, *, athlete_id: UUID, session_id: UUID, slot_id: UUID, skipped: bool
    ) -> Session:
        session = await self.get(athlete_id=athlete_id, session_id=session_id)
        session.skip(slot_id=slot_id, skipped=skipped)
        await self._sessions.save(session=session)
        return session

    async def finish(self, *, athlete_id: UUID, session_id: UUID) -> Session:
        session = await self.get(athlete_id=athlete_id, session_id=session_id)
        session.finish(datetime.now(UTC))
        await self._sessions.save(session=session)
        return session

    async def correct_times(
        self, *, athlete_id: UUID, session_id: UUID, started_at: datetime, ended_at: datetime | None
    ) -> Session:
        session = await self.get(athlete_id=athlete_id, session_id=session_id)
        session.correct_times(started_at=started_at, ended_at=ended_at, now=datetime.now(UTC))
        await self._sessions.save(session=session)
        return session

    async def timer(
        self, *, athlete_id: UUID, session_id: UUID, delta_seconds: int | None
    ) -> Session:
        session = await self.get(athlete_id=athlete_id, session_id=session_id)
        session.adjust_timer(delta_seconds=delta_seconds, now=datetime.now(UTC))
        await self._sessions.save(session=session)
        return session
