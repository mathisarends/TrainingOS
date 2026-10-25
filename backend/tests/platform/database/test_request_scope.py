import httpx
import pytest
from dishka.integrations.fastapi import FromDishka
from fastapi_canon import Feature

from backend.app import create_app
from backend.features.auth.presentation import CurrentUser
from backend.features.exercises.application import ExerciseService
from backend.features.exercises.domain import Category
from backend.platform.api.router import protected_router
from backend.shared import Conflict
from tests.fakes import GoogleTestProvider
from tests.support import sign_in

pytestmark = pytest.mark.integration


async def test_failed_request_rolls_back_already_flushed_writes(database_url: str) -> None:
    router = protected_router(prefix="/scope-probe", tag="test")

    @router.post("", operation_id="test_rollback_probe", status_code=204, response_model=None)
    async def failing_write(
        user: CurrentUser, exercise_service: FromDishka[ExerciseService]
    ) -> None:
        await exercise_service.create(
            user_id=user.id, name="Must roll back", category=Category.BACK, main=False
        )
        raise Conflict("Deliberate failure after database flush")

    # Include through a fresh Composition: Canon must handle the failure after the function scope exits.
    application = create_app(
        Feature(name="fake-google", providers=[GoogleTestProvider]),
        Feature(name="scope-probe", routers=[router]),
    )
    async with application.router.lifespan_context(application):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=application),
            base_url="http://test",
            headers={"Origin": "http://localhost:5173"},
        ) as browser:
            await sign_in(browser)
            before = (await browser.get("/api/v1/exercises")).json()
            failed = await browser.post("/api/v1/scope-probe")
            assert failed.status_code == 409
            assert (await browser.get("/api/v1/exercises")).json() == before
