import asyncio
import os

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine

from backend.features.exercises.infrastructure.repository import SqlExerciseRepository
from backend.platform.database.orm import ExerciseRow, LoginRow, PasswordCredentialRow, UserRow

pytestmark = [pytest.mark.integration, pytest.mark.contract]
ORIGIN = {"Origin": "http://localhost:5173"}
CREDENTIALS = {"email": "training@example.com", "password": "  My training password 2026!  "}


def browser(app: FastAPI, **kwargs: object) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test", headers=ORIGIN
    )


async def test_register_persists_credentials_catalog_and_cookie_after_request_scope(
    app: FastAPI,
    database_url: str,
) -> None:
    async with browser(app) as first:
        response = await first.post("/api/v1/auth/register", json=CREDENTIALS)
        assert response.status_code == 201, response.text
        user_id = response.json()["id"]
        assert response.headers["cache-control"] == "no-store"
        assert "HttpOnly" in response.headers["set-cookie"]
        assert "SameSite=lax" in response.headers["set-cookie"]
        assert "password" not in response.text and "token" not in response.text
        cookie = first.cookies
    # The producer request and client are closed before observing persistence.
    async with browser(app) as restored:
        restored.cookies.update(cookie)
        assert (await restored.get("/api/v1/auth/me")).json()["id"] == user_id
        assert len((await restored.get("/api/v1/exercises")).json()["items"]) == 19
        exported = await restored.get("/api/v1/users/me/export")
        assert exported.json()["login_email"] == CREDENTIALS["email"]
        assert "argon2" not in exported.text and CREDENTIALS["password"] not in exported.text
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as connection:
            encoded = await connection.scalar(select(PasswordCredentialRow.password_hash))
            assert encoded.startswith("$argon2id$")
            assert CREDENTIALS["password"] not in encoded
    finally:
        await engine.dispose()


async def test_login_normalizes_email_preserves_password_and_rotates_browser_session(
    app: FastAPI,
) -> None:
    async with browser(app) as client:
        registered = await client.post("/api/v1/auth/register", json=CREDENTIALS)
        original_token = client.cookies.get("trainingos_session")
        response = await client.post(
            "/api/v1/auth/login", json=CREDENTIALS | {"email": " TRAINING@EXAMPLE.COM "}
        )
        assert response.status_code == 200
        assert response.json()["id"] == registered.json()["id"]
        assert client.cookies.get("trainingos_session") != original_token
        assert (
            await client.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {original_token}"}
            )
        ).status_code == 401
        stripped = await client.post(
            "/api/v1/auth/login", json=CREDENTIALS | {"password": CREDENTIALS["password"].strip()}
        )
        assert stripped.status_code == 401
        assert len((await client.get("/api/v1/exercises")).json()["items"]) == 19
        token = client.cookies.get("trainingos_session")
        assert (await client.post("/api/v1/auth/logout")).status_code == 204
        assert (
            await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        ).status_code == 401


async def test_failed_logins_do_not_reveal_account_existence(app: FastAPI) -> None:
    async with browser(app) as client:
        await client.post("/api/v1/auth/register", json=CREDENTIALS)
        await client.post("/api/v1/auth/logout")
        failures = []
        for email in (CREDENTIALS["email"], "unknown@example.com"):
            response = await client.post(
                "/api/v1/auth/login", json={"email": email, "password": "incorrect password"}
            )
            assert response.status_code == 401
            failures.append((response.json()["code"], response.json()["detail"]))
            assert "trainingos_session" not in client.cookies
        assert failures[0] == failures[1]


async def test_duplicate_registration_keeps_existing_account_and_catalog(
    app: FastAPI, database_url: str
) -> None:
    async with browser(app) as client:
        first = await client.post("/api/v1/auth/register", json=CREDENTIALS)
        duplicate = await client.post(
            "/api/v1/auth/register", json=CREDENTIALS | {"email": "TRAINING@example.com"}
        )
        assert duplicate.status_code == 409
        assert (await client.get("/api/v1/auth/me")).json()["id"] == first.json()["id"]
        assert len((await client.get("/api/v1/exercises")).json()["items"]) == 19
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as connection:
            assert await connection.scalar(select(func.count()).select_from(UserRow)) == 1
    finally:
        await engine.dispose()


@pytest.mark.parametrize(
    "updates",
    [
        {"email": "invalid"},
        {"password": "short"},
        {"password": "s" * 129},
        {"unknown": "unexpected"},
    ],
)
async def test_invalid_registration_returns_safe_validation_errors(
    app: FastAPI, updates: dict
) -> None:
    async with browser(app) as client:
        payload = CREDENTIALS | updates
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422
        assert payload["password"] not in response.text
        assert (await client.get("/api/v1/auth/me")).status_code == 401


@pytest.mark.parametrize("path", ["/register", "/login"])
async def test_password_endpoints_require_origin_even_with_authorization_header(
    app: FastAPI, path: str
) -> None:
    async with browser(app) as client:
        for headers in (
            {"Origin": "https://untrusted.example"},
            {"Origin": "https://untrusted.example", "Authorization": "Bearer arbitrary"},
        ):
            assert (
                await client.post("/api/v1/auth" + path, json=CREDENTIALS, headers=headers)
            ).status_code == 403


async def test_credential_throttle_survives_failed_request_rollbacks(app: FastAPI) -> None:
    async with browser(app) as client:
        for _ in range(10):
            assert (await client.post("/api/v1/auth/login", json=CREDENTIALS)).status_code == 401
        response = await client.post("/api/v1/auth/login", json=CREDENTIALS)
        assert response.status_code == 429
        assert response.headers["Retry-After"] == "300"
        assert response.json()["code"] == "rate_limited"


async def test_account_deletion_removes_local_credentials(app: FastAPI) -> None:
    async with browser(app) as client:
        first = await client.post("/api/v1/auth/register", json=CREDENTIALS)
        assert (await client.delete("/api/v1/users/me")).status_code == 204
        assert (await client.post("/api/v1/auth/login", json=CREDENTIALS)).status_code == 401
        recreated = await client.post("/api/v1/auth/register", json=CREDENTIALS)
        assert recreated.status_code == 201
        assert recreated.json()["id"] != first.json()["id"]


async def test_registration_rolls_back_all_rows_when_catalog_seeding_fails(
    app: FastAPI,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = SqlExerciseRepository.save

    async def fail_after_flush(self: SqlExerciseRepository, *, exercise: object) -> None:
        await original(self, exercise=exercise)
        raise RuntimeError("Simulated failure")

    monkeypatch.setattr(SqlExerciseRepository, "save", fail_after_flush)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
        headers=ORIGIN,
    ) as client:
        assert (await client.post("/api/v1/auth/register", json=CREDENTIALS)).status_code == 500
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as connection:
            for table in (UserRow, PasswordCredentialRow, LoginRow, ExerciseRow):
                assert await connection.scalar(select(func.count()).select_from(table)) == 0
    finally:
        await engine.dispose()


@pytest.mark.postgres
@pytest.mark.skipif(
    not os.environ.get("TRAININGOS_TEST_POSTGRES_URL"),
    reason="Requires dedicated PostgreSQL test URL",
)
async def test_concurrent_registration_creates_one_user(app: FastAPI) -> None:
    async with browser(app) as first, browser(app) as second:
        responses = await asyncio.wait_for(
            asyncio.gather(
                first.post("/api/v1/auth/register", json=CREDENTIALS),
                second.post("/api/v1/auth/register", json=CREDENTIALS),
            ),
            timeout=10,
        )
        assert sorted(r.status_code for r in responses) == [201, 409]
