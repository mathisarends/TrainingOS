from dataclasses import replace
from uuid import UUID

from backend.features.exercises.domain import Category, Exercise, ExerciseRepository
from backend.features.plans.domain import PlanRepository
from backend.features.sessions.domain import SessionRepository
from backend.shared import Conflict, NotFound


class ExerciseService:
    def __init__(
        self,
        exercise_repository: ExerciseRepository,
        session_repository: SessionRepository,
        plan_repository: PlanRepository,
    ) -> None:
        self._exercises, self._sessions, self._plans = (
            exercise_repository,
            session_repository,
            plan_repository,
        )

    async def list(self, *, athlete_id: UUID) -> list[Exercise]:
        return await self._exercises.list(athlete_id=athlete_id)

    async def create(
        self, *, athlete_id: UUID, name: str, category: Category, main: bool
    ) -> Exercise:
        exercise = Exercise(athlete_id=athlete_id, name=name, category=category, main=main)
        await self._exercises.save(exercise=exercise)
        return exercise

    async def revise(
        self, *, athlete_id: UUID, exercise_id: UUID, name: str, category: Category, main: bool
    ) -> Exercise:
        exercise = await self._exercises.get(athlete_id=athlete_id, exercise_id=exercise_id)
        if exercise is None:
            raise NotFound
        exercise.revise(name=name, category=category, main=main)
        await self._exercises.save(exercise=exercise)
        for plan in await self._plans.list(athlete_id=athlete_id):
            changed = False
            for day in plan.days:
                if any(slot.exercise_id == exercise_id for slot in day.slots):
                    slots = tuple(
                        replace(slot, exercise_name=name, category=category, main=main)
                        if slot.exercise_id == exercise_id
                        else slot
                        for slot in day.slots
                    )
                    plan.replace_day(replace(day, slots=slots))
                    changed = True
            if changed:
                await self._plans.save(plan=plan)
        return exercise

    async def remove(self, *, athlete_id: UUID, exercise_id: UUID) -> None:
        exercise = await self._exercises.get(athlete_id=athlete_id, exercise_id=exercise_id)
        if exercise is None:
            raise NotFound
        sessions = await self._sessions.list(athlete_id=athlete_id)
        if any(
            slot.exercise_id == exercise_id and slot.sets
            for session in sessions
            for slot in session.slots
        ):
            exercise.archive()
            await self._exercises.save(exercise=exercise)
            return
        plans = await self._plans.list(athlete_id=athlete_id)
        if any(
            slot.exercise_id == exercise_id
            for plan in plans
            for day in plan.days
            for slot in day.slots
        ):
            raise Conflict("Remove this exercise from plan slots before deleting it")
        await self._exercises.delete(athlete_id=athlete_id, exercise_id=exercise_id)
