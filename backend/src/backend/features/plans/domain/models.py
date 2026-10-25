from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from backend.features.exercises.domain import Category
from backend.features.training.domain import validate_effort
from backend.shared import Aggregate, Conflict, InvalidInput, NotFound


class PlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ENDED = "ended"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class Prescription:
    week: int
    sets: int
    reps: int
    target_rpe: Decimal
    note: str = ""

    def __post_init__(self) -> None:
        if not 1 <= self.week <= 104 or not 1 <= self.sets <= 100 or not 1 <= self.reps <= 100:
            raise InvalidInput("Invalid prescription bounds")
        validate_effort(self.target_rpe)


@dataclass(frozen=True)
class Slot:
    id: UUID
    exercise_id: UUID
    exercise_name: str
    category: Category
    main: bool
    rest_seconds: int
    prescriptions: tuple[Prescription, ...] = ()

    def prescription(self, week: int) -> Prescription:
        for item in self.prescriptions:
            if item.week == week:
                return item
        raise Conflict("A prescription is missing for this week")


@dataclass(frozen=True)
class TrainingDay:
    id: UUID
    name: str
    weekday: int
    slots: tuple[Slot, ...] = ()


class Plan(Aggregate):
    def __init__(
        self,
        *,
        user_id: UUID,
        title: str,
        start_date: date,
        weeks: int,
        days: tuple[TrainingDay, ...],
        status: PlanStatus = PlanStatus.DRAFT,
        recommendations: bool = True,
        revision: int = 1,
        id: UUID | None = None,
    ) -> None:
        super().__init__(id=id)
        if not 1 <= weeks <= 104 or not days:
            raise InvalidInput("A plan needs 1–104 weeks and at least one training day")
        self._user_id, self._title, self._start_date, self._weeks = (
            user_id,
            title,
            start_date,
            weeks,
        )
        self._days, self._status = days, status
        self._recommendations, self._revision = recommendations, revision

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def start_date(self) -> date:
        return self._start_date

    @property
    def weeks(self) -> int:
        return self._weeks

    @property
    def days(self) -> tuple[TrainingDay, ...]:
        return self._days

    @property
    def status(self) -> PlanStatus:
        return self._status

    @property
    def recommendations(self) -> bool:
        return self._recommendations

    @property
    def revision(self) -> int:
        return self._revision

    def day(self, day_id: UUID) -> TrainingDay:
        for day in self.days:
            if day.id == day_id:
                return day
        raise NotFound

    def set_status(self, status: PlanStatus) -> None:
        self._status = status
        self._revision += 1

    def configure(self, *, title: str, start_date: date, recommendations: bool) -> None:
        self._title, self._start_date, self._recommendations = title, start_date, recommendations
        self._revision += 1

    def replace_day(self, day: TrainingDay) -> None:
        self.day(day.id)
        self._days = tuple(day if item.id == day.id else item for item in self.days)
        self._revision += 1

    def prescribe(self, *, slot_id: UUID, prescription: Prescription) -> None:
        if prescription.week > self.weeks:
            raise InvalidInput("Week exceeds plan length")
        for day in self.days:
            for slot in day.slots:
                if slot.id == slot_id:
                    updated = replace(
                        slot,
                        prescriptions=tuple(
                            sorted(
                                [p for p in slot.prescriptions if p.week != prescription.week]
                                + [prescription],
                                key=lambda p: p.week,
                            )
                        ),
                    )
                    self.replace_day(
                        replace(
                            day, slots=tuple(updated if s.id == slot_id else s for s in day.slots)
                        )
                    )
                    return
        raise NotFound

    def copy_week(self, week: int) -> None:
        if not 1 <= week <= self.weeks:
            raise InvalidInput("Week exceeds plan length")
        for day in self.days:
            for slot in day.slots:
                source = slot.prescription(week)
                for target in range(week + 1, self.weeks + 1):
                    self.prescribe(slot_id=slot.id, prescription=replace(source, week=target))

    def progress(self, *, increment: Decimal, deload: bool) -> None:
        if increment not in (Decimal("0.5"), Decimal(1)):
            raise InvalidInput("Progression increment must be 0.5 or 1")
        if deload and self.weeks < 2:
            raise InvalidInput("Deload requires at least two weeks")
        for day in self.days:
            for slot in day.slots:
                source = slot.prescription(1)
                for week in range(2, self.weeks + 1):
                    target = min(
                        Decimal(9 if slot.main else 10), source.target_rpe + increment * (week - 1)
                    )
                    sets = source.sets
                    if deload and week == self.weeks:
                        sets = max(1, sets - 1)
                        target = Decimal(6 if slot.main else 7)
                    self.prescribe(
                        slot_id=slot.id,
                        prescription=replace(source, week=week, sets=sets, target_rpe=target),
                    )

    def duplicate(self, *, user_id: UUID, title: str, start_date: date) -> "Plan":
        days = tuple(
            replace(day, id=uuid4(), slots=tuple(replace(slot, id=uuid4()) for slot in day.slots))
            for day in self.days
        )
        return Plan(
            user_id=user_id,
            title=title,
            start_date=start_date,
            weeks=self.weeks,
            days=days,
            recommendations=self.recommendations,
        )
