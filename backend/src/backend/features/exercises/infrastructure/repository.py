from uuid import UUID

from sqlalchemy import delete
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.features.exercises.domain import (
    Category,
    CategoryDefaults,
    Exercise,
    ExerciseRepository,
)
from backend.platform.database.orm import CategoryDefaultsRow, ExerciseRow


def to_domain(row: ExerciseRow) -> Exercise:
    return Exercise(
        id=row.id,
        user_id=row.user_id,
        name=row.name,
        category=Category(row.category),
        main=row.main,
        archived=row.archived,
    )


class SqlExerciseRepository(ExerciseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_defaults(self, *, user_id: UUID) -> list[CategoryDefaults]:
        rows = await self._session.exec(
            select(CategoryDefaultsRow).where(col(CategoryDefaultsRow.user_id) == user_id)
        )
        return [
            CategoryDefaults(
                Category(row.category), row.rest_seconds, row.sets, row.reps, row.target_rpe
            )
            for row in rows
        ]

    async def save_defaults(self, *, user_id: UUID, defaults: CategoryDefaults) -> None:
        await self._session.merge(
            CategoryDefaultsRow(
                user_id=user_id,
                category=defaults.category,
                rest_seconds=defaults.rest_seconds,
                sets=defaults.sets,
                reps=defaults.reps,
                target_rpe=defaults.target_rpe,
            )
        )
        await self._session.flush()

    async def list(self, *, user_id: UUID) -> list[Exercise]:
        rows = await self._session.exec(
            select(ExerciseRow)
            .where(col(ExerciseRow.user_id) == user_id)
            .order_by(col(ExerciseRow.name), col(ExerciseRow.id))
        )
        return [to_domain(row) for row in rows]

    async def get(self, *, user_id: UUID, exercise_id: UUID) -> Exercise | None:
        row = (
            await self._session.exec(
                select(ExerciseRow).where(
                    col(ExerciseRow.user_id) == user_id, col(ExerciseRow.id) == exercise_id
                )
            )
        ).one_or_none()
        return to_domain(row) if row else None

    async def save(self, *, exercise: Exercise) -> None:
        row = ExerciseRow(
            id=exercise.id,
            user_id=exercise.user_id,
            name=exercise.name,
            category=exercise.category,
            main=exercise.main,
            archived=exercise.archived,
        )
        await self._session.merge(row)
        await self._session.flush()

    async def delete(self, *, user_id: UUID, exercise_id: UUID) -> None:
        await self._session.exec(
            delete(ExerciseRow).where(
                col(ExerciseRow.user_id) == user_id, col(ExerciseRow.id) == exercise_id
            )
        )
