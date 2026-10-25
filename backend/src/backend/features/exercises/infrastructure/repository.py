from uuid import UUID

from sqlalchemy import delete
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.features.exercises.domain import Category, Exercise, ExerciseRepository
from backend.platform.database.orm import ExerciseRow


def to_domain(row: ExerciseRow) -> Exercise:
    return Exercise(
        id=row.id,
        athlete_id=row.athlete_id,
        name=row.name,
        category=Category(row.category),
        main=row.main,
        archived=row.archived,
    )


class SqlExerciseRepository(ExerciseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, *, athlete_id: UUID) -> list[Exercise]:
        rows = await self._session.exec(
            select(ExerciseRow)
            .where(col(ExerciseRow.athlete_id) == athlete_id)
            .order_by(col(ExerciseRow.name), col(ExerciseRow.id))
        )
        return [to_domain(row) for row in rows]

    async def get(self, *, athlete_id: UUID, exercise_id: UUID) -> Exercise | None:
        row = (
            await self._session.exec(
                select(ExerciseRow).where(
                    col(ExerciseRow.athlete_id) == athlete_id, col(ExerciseRow.id) == exercise_id
                )
            )
        ).one_or_none()
        return to_domain(row) if row else None

    async def save(self, *, exercise: Exercise) -> None:
        row = ExerciseRow(
            id=exercise.id,
            athlete_id=exercise.athlete_id,
            name=exercise.name,
            category=exercise.category,
            main=exercise.main,
            archived=exercise.archived,
        )
        await self._session.merge(row)
        await self._session.flush()

    async def delete(self, *, athlete_id: UUID, exercise_id: UUID) -> None:
        await self._session.execute(
            delete(ExerciseRow).where(
                col(ExerciseRow.athlete_id) == athlete_id, col(ExerciseRow.id) == exercise_id
            )
        )
