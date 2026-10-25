from dataclasses import dataclass
from uuid import UUID

from backend.features.athletes.domain import Athlete, AthleteRepository, Preferences
from backend.features.bodyweight.domain import BodyweightRepository, WeighIn
from backend.features.exercises.domain import Exercise, ExerciseRepository
from backend.features.plans.domain import Plan, PlanRepository
from backend.features.sessions.domain import Session, SessionRepository
from backend.shared import NotFound


@dataclass(frozen=True)
class AccountExport:
    athlete: Athlete
    exercises: list[Exercise]
    plans: list[Plan]
    sessions: list[Session]
    bodyweight: list[WeighIn]


class AthleteService:
    def __init__(
        self,
        athlete_repository: AthleteRepository,
        exercise_repository: ExerciseRepository,
        plan_repository: PlanRepository,
        session_repository: SessionRepository,
        bodyweight_repository: BodyweightRepository,
    ) -> None:
        self._athletes, self._exercises, self._plans = (
            athlete_repository,
            exercise_repository,
            plan_repository,
        )
        self._sessions, self._bodyweight = session_repository, bodyweight_repository

    async def configure(self, *, athlete_id: UUID, preferences: Preferences) -> Athlete:
        athlete = await self._athletes.get(athlete_id=athlete_id)
        if athlete is None:
            raise NotFound
        athlete.configure(preferences)
        await self._athletes.save(athlete=athlete)
        return athlete

    async def delete(self, *, athlete_id: UUID) -> None:
        await self._athletes.delete(athlete_id=athlete_id)

    async def export(self, *, athlete_id: UUID) -> AccountExport:
        athlete = await self._athletes.get(athlete_id=athlete_id)
        if athlete is None:
            raise NotFound
        return AccountExport(
            athlete=athlete,
            exercises=await self._exercises.list(athlete_id=athlete_id),
            plans=await self._plans.list(athlete_id=athlete_id),
            sessions=await self._sessions.list(athlete_id=athlete_id),
            bodyweight=await self._bodyweight.list(athlete_id=athlete_id),
        )
