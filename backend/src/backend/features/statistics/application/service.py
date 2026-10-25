from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from backend.features.athletes.domain import Preferences
from backend.features.exercises.domain import Category, ExerciseRepository
from backend.features.sessions.domain import SessionRepository
from backend.features.training.domain import e1rm


@dataclass(frozen=True)
class WeeklyVolume:
    plan_id: UUID
    week: int
    category: Category
    tonnage_kg: Decimal
    work_sets: int


@dataclass(frozen=True)
class StrengthPoint:
    exercise_id: UUID
    session_id: UUID
    plan_id: UUID
    performed_at: datetime
    e1rm_kg: Decimal


@dataclass(frozen=True)
class DurationPoint:
    session_id: UUID
    started_at: datetime
    duration_seconds: int


@dataclass(frozen=True)
class Statistics:
    tonnage_kg: Decimal
    work_sets: int
    weekly_volume: tuple[WeeklyVolume, ...]
    strength: tuple[StrengthPoint, ...]
    records: tuple[StrengthPoint, ...]
    durations: tuple[DurationPoint, ...]
    activity_dates: tuple[date, ...]


class StatisticsService:
    def __init__(
        self, session_repository: SessionRepository, exercise_repository: ExerciseRepository
    ) -> None:
        self._sessions, self._exercises = session_repository, exercise_repository

    async def calculate(
        self, *, athlete_id: UUID, preferences: Preferences, plan_id: UUID | None = None
    ) -> Statistics:
        sessions = await self._sessions.list(athlete_id=athlete_id)
        main_ids = {
            exercise.id
            for exercise in await self._exercises.list(athlete_id=athlete_id)
            if exercise.main
        }
        volume: dict[tuple[UUID, int, Category], Decimal] = {}
        counts: dict[tuple[UUID, int, Category], int] = {}
        strength: list[StrengthPoint] = []
        durations: list[DurationPoint] = []
        activity: set[date] = set()
        for session in sessions:
            if plan_id is not None and session.plan_id != plan_id:
                continue
            activity.add(session.started_at.astimezone(ZoneInfo(preferences.timezone)).date())
            if session.duration_seconds is not None:
                durations.append(
                    DurationPoint(
                        session_id=session.id,
                        started_at=session.started_at,
                        duration_seconds=session.duration_seconds,
                    )
                )
            best: dict[UUID, Decimal] = {}
            for slot in session.slots:
                key = (session.plan_id, session.week, slot.category)
                for item in slot.sets:
                    volume[key] = volume.get(key, Decimal(0)) + item.weight_kg * item.reps
                    counts[key] = counts.get(key, 0) + 1
                    if slot.exercise_id in main_ids:
                        maximum = e1rm(
                            weight_kg=item.weight_kg,
                            reps=item.reps,
                            rpe=item.rpe,
                            preferences=preferences,
                        )
                        best[slot.exercise_id] = max(
                            best.get(slot.exercise_id, Decimal(0)), maximum
                        )
            for exercise_id, maximum in best.items():
                strength.append(
                    StrengthPoint(
                        exercise_id=exercise_id,
                        session_id=session.id,
                        plan_id=session.plan_id,
                        performed_at=session.started_at,
                        e1rm_kg=maximum,
                    )
                )
        records: list[StrengthPoint] = []
        best_so_far: dict[UUID, Decimal] = {}
        for point in strength:
            if point.e1rm_kg > best_so_far.get(point.exercise_id, Decimal(0)):
                records.append(point)
                best_so_far[point.exercise_id] = point.e1rm_kg
        weekly = tuple(
            WeeklyVolume(
                plan_id=key[0],
                week=key[1],
                category=key[2],
                tonnage_kg=value,
                work_sets=counts[key],
            )
            for key, value in sorted(volume.items())
        )
        return Statistics(
            tonnage_kg=sum(volume.values(), Decimal(0)),
            work_sets=sum(counts.values()),
            weekly_volume=weekly,
            strength=tuple(strength),
            records=tuple(records),
            durations=tuple(durations),
            activity_dates=tuple(sorted(activity)),
        )
