import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4

import asyncpg
import httpx
import pytest
from alembic import command
from backend.app import create_app
from backend.features.auth.domain import ExternalIdentity, IdentityProvider
from backend.platform.database.migrations import migration_config
from backend.shared import AuthenticationRequired
from dishka import Provider, Scope, provide
from fastapi import FastAPI
from fastapi_canon import Feature
from sqlalchemy.engine import make_url

from tests.support import sign_in


class FakeGoogle(IdentityProvider):
    """Only the nondeterministic Google boundary is scripted; auth/SQL/transactions are real."""

    def authorize_url(self, *, state: str, verifier: str, nonce: str) -> str:
        return "https://accounts.google.test/authorize?" + urlencode({"state": state})

    async def exchange(self, *, code: str, verifier: str, nonce: str) -> ExternalIdentity:
        if code == "invalid":
            raise AuthenticationRequired
        return ExternalIdentity(issuer="https://accounts.google.com", subject=code)


class GoogleTestProvider(Provider):
    @provide(scope=Scope.APP, override=True)
    def google(self) -> IdentityProvider:
        return FakeGoogle()


@pytest.fixture
def database_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    url = f"sqlite+aiosqlite:///{tmp_path / 'trainingos.db'}"
    postgres_url = os.environ.get("TRAININGOS_TEST_POSTGRES_URL")
    database_name = "trainingos_test_" + uuid4().hex
    if postgres_url:
        parsed = make_url(postgres_url)
        if parsed.database is None or "test" not in parsed.database:
            raise ValueError(
                "The PostgreSQL test URL must point to an explicitly named test database"
            )

        async def create_database() -> None:
            connection = await asyncpg.connect(
                postgres_url.replace("postgresql+asyncpg:", "postgresql:")
            )
            try:
                await connection.execute(f'CREATE DATABASE "{database_name}"')
            finally:
                await connection.close()

        asyncio.run(create_database())
        url = parsed.set(database=database_name).render_as_string(hide_password=False)
    monkeypatch.setenv("TRAININGOS_DATABASE_URL", url)
    monkeypatch.setenv("TRAININGOS_ENVIRONMENT", "local")
    monkeypatch.setenv("TRAININGOS_SECURE_COOKIES", "false")
    monkeypatch.setenv("TRAININGOS_ALLOWED_ORIGINS", '["http://localhost:5173"]')
    try:
        command.upgrade(migration_config(), "head")
        yield url
    finally:
        if postgres_url:

            async def drop_database() -> None:
                connection = await asyncpg.connect(
                    postgres_url.replace("postgresql+asyncpg:", "postgresql:")
                )
                try:
                    await connection.execute(f'DROP DATABASE "{database_name}" WITH (FORCE)')
                finally:
                    await connection.close()

            asyncio.run(drop_database())


@pytest.fixture
async def app(database_url: str) -> AsyncIterator[FastAPI]:
    application = create_app(Feature(name="fake-google", providers=[GoogleTestProvider]))
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        headers={"Origin": "http://localhost:5173"},
    ) as client:
        await sign_in(client)
        yield client


@pytest.fixture
async def other_client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        headers={"Origin": "http://localhost:5173"},
    ) as client:
        await sign_in(client, "athlete-b")
        yield client
