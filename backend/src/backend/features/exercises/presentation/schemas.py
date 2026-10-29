from decimal import Decimal
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


class CategoryDefaultsRequest(Schema):
    rest_seconds: int = Field(ge=0, le=3600)
    sets: int = Field(ge=1, le=100)
    reps: int = Field(ge=1, le=100)
    target_effort: Decimal


class CategoryDefaultsResponse(Schema):
    category: Category
    rest_seconds: int
    sets: int
    reps: int
    target_rpe: Decimal
    target_effort: Decimal


class CategoryDefaultsListResponse(Schema):
    items: list[CategoryDefaultsResponse]
