from uuid import UUID

from pydantic import Field

from backend.features.exercises.domain import Category
from backend.platform.api.schema import Schema


class ExerciseRequest(Schema):
    name: str = Field(min_length=1, max_length=200)
    category: Category
    main: bool = False


class ExerciseResponse(Schema):
    id: UUID
    name: str
    category: Category
    main: bool
    archived: bool


class ExerciseListResponse(Schema):
    items: list[ExerciseResponse]
