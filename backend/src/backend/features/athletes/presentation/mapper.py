from backend.features.athletes.domain import Athlete

from .schemas import AthleteResponse


def to_response(athlete: Athlete) -> AthleteResponse:
    preferences = athlete.preferences
    return AthleteResponse(
        id=athlete.id,
        unit=preferences.unit,
        rounding_step=preferences.rounding_step,
        effort_scale=preferences.effort_scale,
        target_weight=preferences.from_kg(preferences.target_weight_kg)
        if preferences.target_weight_kg is not None
        else None,
        timezone=preferences.timezone,
    )
