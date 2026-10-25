from backend.features.exercises.domain import Exercise

from .schemas import ExerciseListResponse, ExerciseResponse


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
