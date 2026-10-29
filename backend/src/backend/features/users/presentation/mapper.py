from backend.features.users.domain import User

from .schemas import UserResponse


def to_response(user: User) -> UserResponse:
    preferences = user.preferences
    return UserResponse(
        id=user.id,
        unit=preferences.unit,
        rounding_step=preferences.rounding_step,
        effort_scale=preferences.effort_scale,
        timezone=preferences.timezone,
    )
