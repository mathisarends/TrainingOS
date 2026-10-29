from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi_canon import CanonRouter

from backend.features.auth.application import AuthService, GoogleAuthService
from backend.features.users.presentation.mapper import to_response
from backend.features.users.presentation.schemas import UserResponse
from backend.platform.api.errors import (
    authentication_required,
    conflict,
    errors,
    forbidden,
    invalid_input,
    provider_unavailable,
    rate_limited,
)
from backend.settings import AppSettings

from .cookies import AuthCookies
from .dependencies import CurrentUser
from .schemas import CredentialsRequest

router = CanonRouter(prefix="/auth", tags=["auth"], route_class=DishkaRoute, error_registry=errors)


@router.post(
    "/register",
    operation_id="register_user",
    status_code=201,
    response_model=UserResponse,
    raises=[authentication_required, conflict, invalid_input, forbidden, rate_limited],
)
async def register(
    body: CredentialsRequest,
    request: Request,
    response: Response,
    auth_service: FromDishka[AuthService],
    auth_cookies: FromDishka[AuthCookies],
) -> UserResponse:
    auth_cookies.verify_origin(request, allow_bearer=False)
    signed_in = await auth_service.password_register(
        email=str(body.email),
        password=body.password.get_secret_value(),
        client_key=request.client.host if request.client else "unknown",
    )
    await auth_service.logout(token=auth_cookies.token(request))
    auth_cookies.set_session(response, signed_in.token)
    return to_response(signed_in.user)


@router.post(
    "/login",
    operation_id="login_user",
    status_code=200,
    response_model=UserResponse,
    raises=[authentication_required, forbidden, rate_limited],
)
async def login(
    body: CredentialsRequest,
    request: Request,
    response: Response,
    auth_service: FromDishka[AuthService],
    auth_cookies: FromDishka[AuthCookies],
) -> UserResponse:
    auth_cookies.verify_origin(request, allow_bearer=False)
    signed_in = await auth_service.password_login(
        email=str(body.email),
        password=body.password.get_secret_value(),
        client_key=request.client.host if request.client else "unknown",
    )
    await auth_service.logout(token=auth_cookies.token(request))
    auth_cookies.set_session(response, signed_in.token)
    return to_response(signed_in.user)


@router.get(
    "/google/login",
    operation_id="start_google_login",
    status_code=307,
    response_model=None,
    raises=[provider_unavailable],
)
async def google_login(
    auth_service: FromDishka[GoogleAuthService], auth_cookies: FromDishka[AuthCookies]
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
    responses={303: {"description": "Browser sign-in redirects to the configured frontend"}},
)
async def google_callback(
    request: Request,
    response: Response,
    auth_service: FromDishka[AuthService],
    google_auth: FromDishka[GoogleAuthService],
    auth_cookies: FromDishka[AuthCookies],
    settings: FromDishka[AppSettings],
    code: Annotated[str, Query(min_length=1, max_length=4096)],
    state: Annotated[str, Query(min_length=1, max_length=512)],
) -> UserResponse | RedirectResponse:
    signed_in = await google_auth.google_callback(
        code=code, state=state, expected_state=auth_cookies.oauth_state(request)
    )
    # Replacing a browser login revokes the old application session.
    await auth_service.logout(token=auth_cookies.token(request))
    # Browser navigations return to a fixed, trusted origin; API clients retain JSON.
    if "text/html" in request.headers.get("accept", ""):
        redirect = RedirectResponse(settings.frontend_url, status_code=303)
        auth_cookies.set_session(redirect, signed_in.token)
        auth_cookies.clear_oauth_state(redirect)
        return redirect
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
