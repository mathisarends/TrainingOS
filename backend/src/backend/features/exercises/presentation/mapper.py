from backend.features.exercises.domain import CategoryDefaults, Exercise
from backend.features.users.domain import EffortScale, Preferences

from .schemas import CategoryDefaultsResponse, ExerciseListResponse, ExerciseResponse


def to_defaults_response(
    defaults: CategoryDefaults, preferences: Preferences
) -> CategoryDefaultsResponse:
    return CategoryDefaultsResponse(
        category=defaults.category,
        rest_seconds=defaults.rest_seconds,
        sets=defaults.sets,
        reps=defaults.reps,
        target_rpe=defaults.target_rpe,
        target_effort=10 - defaults.target_rpe
        if preferences.effort_scale == EffortScale.RIR
        else defaults.target_rpe,
    )


def to_response(exercise: Exercise) -> ExerciseResponse:
    return ExerciseResponse(
        id=exercise.id,
        name=exercise.name,
        category=exercise.category,
        main=exercise.main,
        archived=exercise.archived,
    )


def to_list_response(exercises: list[Exercise]) -> ExerciseListResponse:
    return ExerciseListResponse(items=[to_response(exercise) for exercise in exercises])
