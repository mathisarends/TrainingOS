from backend.features.athletes.domain import Preferences
from backend.features.statistics.application import Statistics, StrengthPoint

from .schemas import (
    DurationPointResponse,
    StatisticsResponse,
    StrengthPointResponse,
    WeeklyVolumeResponse,
)


def strength_response(point: StrengthPoint, preferences: Preferences) -> StrengthPointResponse:
    return StrengthPointResponse(
        exercise_id=point.exercise_id,
        session_id=point.session_id,
        plan_id=point.plan_id,
        performed_at=point.performed_at,
        e1rm=preferences.from_kg(point.e1rm_kg),
    )


def to_response(statistics: Statistics, preferences: Preferences) -> StatisticsResponse:
    return StatisticsResponse(
        unit=preferences.unit,
        tonnage=preferences.from_kg(statistics.tonnage_kg),
        work_sets=statistics.work_sets,
        weekly_volume=[
            WeeklyVolumeResponse(
                plan_id=item.plan_id,
                week=item.week,
                category=item.category,
                tonnage=preferences.from_kg(item.tonnage_kg),
                work_sets=item.work_sets,
            )
            for item in statistics.weekly_volume
        ],
        strength=[strength_response(point, preferences) for point in statistics.strength],
        records=[strength_response(point, preferences) for point in statistics.records],
        durations=[
            DurationPointResponse(
                session_id=point.session_id,
                started_at=point.started_at,
                duration_seconds=point.duration_seconds,
            )
            for point in statistics.durations
        ],
        activity_dates=list(statistics.activity_dates),
    )
