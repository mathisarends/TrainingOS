from uuid import UUID

from dishka.integrations.fastapi import FromDishka
from fastapi import Response

from backend.features.auth.presentation import CurrentAthlete
from backend.features.exercises.application import ExerciseService
from backend.platform.api.router import protected_router

from .mapper import to_list_response, to_response
from .schemas import ExerciseListResponse, ExerciseRequest, ExerciseResponse

router = protected_router(prefix="/exercises", tag="exercises")


@router.get("", operation_id="list_exercises", status_code=200, response_model=ExerciseListResponse)
async def list_exercises(
    athlete: CurrentAthlete, exercise_service: FromDishka[ExerciseService]
) -> ExerciseListResponse:
    exercises = await exercise_service.list(athlete_id=athlete.id)
    return to_list_response(exercises)


@router.post("", operation_id="create_exercise", status_code=201, response_model=ExerciseResponse)
async def create_exercise(
    body: ExerciseRequest, athlete: CurrentAthlete, exercise_service: FromDishka[ExerciseService]
) -> ExerciseResponse:
    exercise = await exercise_service.create(
        athlete_id=athlete.id, name=body.name, category=body.category, main=body.main
    )
    return to_response(exercise)


@router.put(
    "/{exercise_id}",
    operation_id="revise_exercise",
    status_code=200,
    response_model=ExerciseResponse,
)
async def revise_exercise(
    exercise_id: UUID,
    body: ExerciseRequest,
    athlete: CurrentAthlete,
    exercise_service: FromDishka[ExerciseService],
) -> ExerciseResponse:
    exercise = await exercise_service.revise(
        athlete_id=athlete.id,
        exercise_id=exercise_id,
        name=body.name,
        category=body.category,
        main=body.main,
    )
    return to_response(exercise)


@router.delete(
    "/{exercise_id}", operation_id="remove_exercise", status_code=204, response_model=None
)
async def remove_exercise(
    exercise_id: UUID, athlete: CurrentAthlete, exercise_service: FromDishka[ExerciseService]
) -> Response:
    await exercise_service.remove(athlete_id=athlete.id, exercise_id=exercise_id)
    return Response(status_code=204)
