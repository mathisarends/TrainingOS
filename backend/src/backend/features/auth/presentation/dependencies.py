from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, Request

from backend.features.auth.application import AuthService
from backend.features.users.domain import User

from .cookies import AuthCookies


@inject
async def get_current_user(
    request: Request, auth_service: FromDishka[AuthService], auth_cookies: FromDishka[AuthCookies]
) -> User:
    auth_cookies.verify_origin(request)
    return await auth_service.current(token=auth_cookies.token(request))


CurrentUser = Annotated[User, Depends(get_current_user)]
