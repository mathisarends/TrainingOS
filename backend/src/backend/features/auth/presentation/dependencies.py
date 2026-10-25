from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, Request

from backend.features.athletes.domain import Athlete
from backend.features.auth.application import AuthService

from .cookies import AuthCookies


@inject
async def get_current_athlete(
    request: Request, auth_service: FromDishka[AuthService], auth_cookies: FromDishka[AuthCookies]
) -> Athlete:
    auth_cookies.verify_origin(request)
    return await auth_service.current(token=auth_cookies.token(request))


CurrentAthlete = Annotated[Athlete, Depends(get_current_athlete)]
