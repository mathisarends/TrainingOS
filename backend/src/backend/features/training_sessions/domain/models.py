from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from backend.features.exercises.domain import Category
from backend.features.plans.domain import Prescription
from backend.features.training.domain import validate_effort
from backend.shared import Aggregate, Conflict, InvalidInput, NotFound


@dataclass(frozen=True)
class WorkSet:
    id: UUID
    weight_kg: Decimal
    reps: int
    rpe: Decimal
    recorded_at: datetime

    def __post_init__(self) -> None:
        if not self.weight_kg.is_finite() or self.weight_kg < 0 or not 1 <= self.reps <= 100:
            raise InvalidInput("Weight must be nonnegative and reps between 1 and 100")
        validate_effort(self.rpe)


@dataclass(frozen=True)
class TrainingSessionSlot:
    id: UUID
    exercise_id: UUID
    exercise_name: str
    category: Category
    main: bool
    rest_seconds: int
    prescription: Prescription
    skipped: bool = False
    sets: tuple[WorkSet, ...] = ()


class TrainingSession(Aggregate):
    def __init__(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
        plan_title: str,
        day_id: UUID,
        day_name: str,
        week: int,
        slots: tuple[TrainingSessionSlot, ...],
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        rest_ends_at: datetime | None = None,
        id: UUID | None = None,
    ) -> None:
        super().__init__(id=id)
        self._user_id, self._plan_id, self._plan_title = user_id, plan_id, plan_title
        self._day_id, self._day_name, self._week = day_id, day_name, week
        self._slots = slots
        self._started_at, self._ended_at = started_at or datetime.now(UTC), ended_at
        self._rest_ends_at = rest_ends_at

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def plan_id(self) -> UUID:
        return self._plan_id

    @property
    def plan_title(self) -> str:
        return self._plan_title

    @property
    def day_id(self) -> UUID:
        return self._day_id

    @property
    def day_name(self) -> str:
        return self._day_name

    @property
    def week(self) -> int:
        return self._week

    @property
    def slots(self) -> tuple[TrainingSessionSlot, ...]:
        return self._slots

    @property
    def started_at(self) -> datetime:
        return self._started_at

    @property
    def ended_at(self) -> datetime | None:
        return self._ended_at

    @property
    def rest_ends_at(self) -> datetime | None:
        return self._rest_ends_at

    @property
    def duration_seconds(self) -> int | None:
        return int((self.ended_at - self.started_at).total_seconds()) if self.ended_at else None

    def slot(self, slot_id: UUID) -> TrainingSessionSlot:
        for slot in self.slots:
            if slot.id == slot_id:
                return slot
        raise NotFound

    def _replace_slot(self, slot: TrainingSessionSlot) -> None:
        self._slots = tuple(slot if item.id == slot.id else item for item in self.slots)

    def record(
        self,
        *,
        slot_id: UUID,
        weight_kg: Decimal,
        reps: int,
        rpe: Decimal,
        now: datetime,
        set_id: UUID | None = None,
    ) -> WorkSet:
        slot = self.slot(slot_id)
        if set_id is not None and not any(item.id == set_id for item in slot.sets):
            raise NotFound
        previous = next((item for item in slot.sets if item.id == set_id), None)
        work_set = WorkSet(
            id=set_id or uuid4(),
            weight_kg=weight_kg,
            reps=reps,
            rpe=rpe,
            recorded_at=previous.recorded_at if previous else now,
        )
        items = tuple(work_set if item.id == set_id else item for item in slot.sets)
        if set_id is None:
            items += (work_set,)
        self._replace_slot(replace(slot, sets=items, skipped=False))
        if self.ended_at is None:
            self._rest_ends_at = now + timedelta(seconds=slot.rest_seconds)
        return work_set

    def remove_set(self, *, slot_id: UUID, set_id: UUID) -> None:
        slot = self.slot(slot_id)
        if not any(item.id == set_id for item in slot.sets):
            raise NotFound
        self._replace_slot(
            replace(slot, sets=tuple(item for item in slot.sets if item.id != set_id))
        )

    def skip(self, *, slot_id: UUID, skipped: bool) -> None:
        slot = self.slot(slot_id)
        if skipped and slot.sets:
            raise Conflict("A slot with recorded sets cannot be skipped")
        self._replace_slot(replace(slot, skipped=skipped))

    def finish(self, now: datetime) -> None:
        if self.ended_at is not None:
            raise Conflict("Training session has already ended")
        self.correct_times(started_at=self.started_at, ended_at=now, now=now)
        self._rest_ends_at = None

    def correct_times(
        self, *, started_at: datetime, ended_at: datetime | None, now: datetime
    ) -> None:
        if started_at > now or (ended_at is not None and not started_at <= ended_at <= now):
            raise InvalidInput(
                "Training session timestamps must be ordered and cannot be in the future"
            )
        if self.ended_at and ended_at is None:
            raise Conflict("A completed session cannot be reopened")
        self._started_at, self._ended_at = started_at, ended_at
        if ended_at:
            self._rest_ends_at = None

    def adjust_timer(self, *, delta_seconds: int | None, now: datetime) -> None:
        if self.ended_at:
            raise Conflict("Training session has ended")
        if delta_seconds is None:
            self._rest_ends_at = None
        else:
            if self.rest_ends_at is None:
                raise Conflict("There is no running timer")
            deadline = self.rest_ends_at + timedelta(seconds=delta_seconds)
            if deadline > now + timedelta(days=1):
                raise InvalidInput("Timer cannot exceed one day")
            self._rest_ends_at = max(now, deadline)
