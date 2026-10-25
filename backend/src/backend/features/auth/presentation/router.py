from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi_canon import CanonRouter

from backend.features.auth.application import AuthService
from backend.features.users.presentation.mapper import to_response
from backend.features.users.presentation.schemas import UserResponse
from backend.platform.api.errors import (
    authentication_required,
    errors,
    forbidden,
    provider_unavailable,
)

from .cookies import AuthCookies
from .dependencies import CurrentUser

router = CanonRouter(prefix="/auth", tags=["auth"], route_class=DishkaRoute, error_registry=errors)


@router.get(
    "/google/login",
    operation_id="start_google_login",
    status_code=307,
    response_model=None,
    raises=[provider_unavailable],
)
async def google_login(
    auth_service: FromDishka[AuthService], auth_cookies: FromDishka[AuthCookies]
) -> RedirectResponse:
    authorization = await auth_service.google_authorization()
    response = RedirectResponse(authorization.url, status_code=307)
    auth_cookies.set_oauth_state(response, authorization.state)
    return response


@router.get(
    "/google/callback",
    operation_id="complete_google_login",
    status_code=200,
    response_model=UserResponse,
    raises=[authentication_required, provider_unavailable],
)
async def google_callback(
    request: Request,
    response: Response,
    auth_service: FromDishka[AuthService],
    auth_cookies: FromDishka[AuthCookies],
    code: Annotated[str, Query(min_length=1, max_length=4096)],
    state: Annotated[str, Query(min_length=1, max_length=512)],
) -> UserResponse:
    signed_in = await auth_service.google_callback(
        code=code, state=state, expected_state=auth_cookies.oauth_state(request)
    )
    # Replacing a browser login revokes the old application session.
    await auth_service.logout(token=auth_cookies.token(request))
    auth_cookies.set_session(response, signed_in.token)
    auth_cookies.clear_oauth_state(response)
    return to_response(signed_in.user)


@router.get(
    "/me",
    operation_id="get_authenticated_user",
    status_code=200,
    response_model=UserResponse,
    raises=[authentication_required, forbidden],
)
async def me(user: CurrentUser, response: Response) -> UserResponse:
    response.headers["Cache-Control"] = "no-store"
    return to_response(user)


@router.post(
    "/logout",
    operation_id="logout_user",
    status_code=204,
    response_model=None,
    raises=[authentication_required, forbidden],
)
async def logout(
    request: Request,
    user: CurrentUser,
    auth_service: FromDishka[AuthService],
    auth_cookies: FromDishka[AuthCookies],
) -> Response:
    await auth_service.logout(token=auth_cookies.token(request))
    response = Response(status_code=204)
    auth_cookies.clear_session(response)
    return response
