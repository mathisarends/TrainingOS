from collections.abc import AsyncGenerator

from dishka import Scope
from fastapi import Request


async def http_request_scope(request: Request) -> AsyncGenerator[None]:
    """Commit before sending success; propagate failures into Dishka finalizers."""
    middleware_container = request.state.dishka_container
    async with request.app.state.dishka_container(
        {Request: request}, scope=Scope.REQUEST
    ) as container:
        request.state.dishka_container = container
        try:
            yield
        finally:
            request.state.dishka_container = middleware_container
