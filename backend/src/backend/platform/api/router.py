from dishka.integrations.fastapi import DishkaRoute
from fastapi_canon import CanonRouter

from .errors import authentication_required, conflict, errors, forbidden, invalid_input, not_found


def protected_router(*, prefix: str, tag: str) -> CanonRouter:
    return CanonRouter(
        prefix=prefix,
        tags=[tag],
        route_class=DishkaRoute,
        error_registry=errors,
        raises=[authentication_required, not_found, conflict, invalid_input, forbidden],
    )
