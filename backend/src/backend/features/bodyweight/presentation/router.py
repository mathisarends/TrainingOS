from uuid import UUID

from dishka.integrations.fastapi import FromDishka
from fastapi import Response

from backend.features.auth.presentation import CurrentAthlete
from backend.features.bodyweight.application import BodyweightService
from backend.platform.api.router import protected_router

from .mapper import to_list_response, to_response
from .schemas import BodyweightResponse, WeighInRequest, WeighInResponse

router = protected_router(prefix="/bodyweight", tag="bodyweight")


@router.get("", operation_id="list_bodyweight", status_code=200, response_model=BodyweightResponse)
async def list_bodyweight(
    athlete: CurrentAthlete, bodyweight_service: FromDishka[BodyweightService]
) -> BodyweightResponse:
    items = await bodyweight_service.list(athlete_id=athlete.id)
    return to_list_response(items, athlete.preferences)


@router.put("", operation_id="record_bodyweight", status_code=200, response_model=WeighInResponse)
async def record_bodyweight(
    body: WeighInRequest, athlete: CurrentAthlete, bodyweight_service: FromDishka[BodyweightService]
) -> WeighInResponse:
    item = await bodyweight_service.record(
        athlete_id=athlete.id, date=body.date, weight_kg=athlete.preferences.to_kg(body.weight)
    )
    return to_response(item, athlete.preferences)


@router.delete(
    "/{weigh_in_id}", operation_id="delete_bodyweight", status_code=204, response_model=None
)
async def delete_bodyweight(
    weigh_in_id: UUID, athlete: CurrentAthlete, bodyweight_service: FromDishka[BodyweightService]
) -> Response:
    await bodyweight_service.remove(athlete_id=athlete.id, weigh_in_id=weigh_in_id)
    return Response(status_code=204)
