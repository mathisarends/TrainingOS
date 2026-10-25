from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from backend.features.athletes.domain import WeightUnit
from backend.features.exercises.domain import Category
from backend.platform.api.schema import Schema


class WeeklyVolumeResponse(Schema):
    plan_id: UUID
    week: int
    category: Category
    tonnage: Decimal
    work_sets: int


class StrengthPointResponse(Schema):
    exercise_id: UUID
    session_id: UUID
    plan_id: UUID
    performed_at: datetime
    e1rm: Decimal


class DurationPointResponse(Schema):
    session_id: UUID
    started_at: datetime
    duration_seconds: int


class StatisticsResponse(Schema):
    unit: WeightUnit
    tonnage: Decimal
    work_sets: int
    weekly_volume: list[WeeklyVolumeResponse]
    strength: list[StrengthPointResponse]
    records: list[StrengthPointResponse]
    durations: list[DurationPointResponse]
    activity_dates: list[date]


class PlanComparisonResponse(Schema):
    first_plan_id: UUID
    second_plan_id: UUID
    first: StatisticsResponse
    second: StatisticsResponse
