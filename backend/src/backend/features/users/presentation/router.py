from dishka.integrations.fastapi import FromDishka
from fastapi import Response

from backend.features.auth.presentation import CurrentUser
from backend.features.auth.presentation.cookies import AuthCookies
from backend.features.users.application import UserService
from backend.features.users.domain import Preferences
from backend.platform.api.router import protected_router

from .export import AccountExportResponse, to_export_response
from .mapper import to_response
from .schemas import PreferencesRequest, UserResponse

router = protected_router(prefix="/users/me", tag="users")


@router.put(
    "/preferences",
    operation_id="configure_user",
    status_code=200,
    response_model=UserResponse,
)
async def configure_user(
    body: PreferencesRequest, user: CurrentUser, user_service: FromDishka[UserService]
) -> UserResponse:
    preferences = Preferences(
        unit=body.unit,
        rounding_step=body.rounding_step,
        effort_scale=body.effort_scale,
        timezone=body.timezone,
    )
    updated = await user_service.configure(user_id=user.id, preferences=preferences)
    return to_response(updated)


@router.get(
    "/export",
    operation_id="export_user_data",
    status_code=200,
    response_model=AccountExportResponse,
)
async def export_user(
    user: CurrentUser, response: Response, user_service: FromDishka[UserService]
) -> AccountExportResponse:
    export = await user_service.export(user_id=user.id)
    response.headers["Content-Disposition"] = 'attachment; filename="trainingos-export.json"'
    response.headers["Cache-Control"] = "no-store"
    return to_export_response(export)


@router.delete("", operation_id="delete_user_account", status_code=204, response_model=None)
async def delete_user(
    user: CurrentUser,
    user_service: FromDishka[UserService],
    auth_cookies: FromDishka[AuthCookies],
) -> Response:
    await user_service.delete(user_id=user.id)
    response = Response(status_code=204)
    auth_cookies.clear_session(response)
    return response
