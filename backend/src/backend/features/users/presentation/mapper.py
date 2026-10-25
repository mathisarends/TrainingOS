from backend.features.users.domain import User

from .schemas import UserResponse


def to_response(user: User) -> UserResponse:
    preferences = user.preferences
    return UserResponse(
        id=user.id,
        unit=preferences.unit,
        rounding_step=preferences.rounding_step,
        effort_scale=preferences.effort_scale,
        target_weight=preferences.from_kg(preferences.target_weight_kg)
        if preferences.target_weight_kg is not None
        else None,
        timezone=preferences.timezone,
    )
