from backend.features.athletes.domain import Preferences
from backend.features.bodyweight.domain import WeighIn

from .schemas import BodyweightResponse, WeighInResponse


def to_response(item: WeighIn, preferences: Preferences) -> WeighInResponse:
    return WeighInResponse(id=item.id, date=item.date, weight=preferences.from_kg(item.weight_kg))


def to_list_response(items: list[WeighIn], preferences: Preferences) -> BodyweightResponse:
    return BodyweightResponse(
        unit=preferences.unit,
        target_weight=preferences.from_kg(preferences.target_weight_kg)
        if preferences.target_weight_kg is not None
        else None,
        items=[to_response(item, preferences) for item in items],
    )
