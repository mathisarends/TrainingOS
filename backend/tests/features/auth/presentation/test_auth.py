from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi import FastAPI

from tests.support import sign_in

pytestmark = [pytest.mark.integration, pytest.mark.contract]


async def test_missing_authentication_returns_problem_details(app: FastAPI) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as anonymous:
        response = await anonymous.get("/api/v1/plans")
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["code"] == "authentication_required"


async def test_first_sign_in_seeds_catalog_only_once(client: httpx.AsyncClient) -> None:
    original = (await client.get("/api/v1/auth/me")).json()
    catalog = (await client.get("/api/v1/exercises")).json()["items"]
    assert len({item["category"] for item in catalog}) == 10
    assert original["unit"] == "kg"
    assert original["rounding_step"] == "2.5"
    again = await sign_in(client)
    assert again["id"] == original["id"]
    assert (await client.get("/api/v1/exercises")).json()["items"] == catalog


async def test_oauth_state_is_browser_bound_and_single_use(app: FastAPI) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as browser:
        started = await browser.get("/api/v1/auth/google/login")
        state = parse_qs(urlparse(started.headers["location"]).query)["state"][0]
        rejected = await browser.get(
            "/api/v1/auth/google/callback", params={"code": "user", "state": "wrong-state"}
        )
        assert rejected.status_code == 401
        assert (await browser.get("/api/v1/auth/me")).status_code == 401
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as other_browser:
            stolen = await other_browser.get(
                "/api/v1/auth/google/callback", params={"code": "user", "state": state}
            )
            assert stolen.status_code == 401
        completed = await browser.get(
            "/api/v1/auth/google/callback", params={"code": "user", "state": state}
        )
        assert completed.status_code == 200
        browser.cookies.set(
            "trainingos_oauth_state", state, domain="test.local", path="/api/v1/auth/google"
        )
        replay = await browser.get(
            "/api/v1/auth/google/callback", params={"code": "user", "state": state}
        )
        assert replay.status_code == 401


async def test_cookie_mutations_require_allowed_origin(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/plans",
        headers={"Origin": "https://untrusted.example"},
        json={
            "title": "CSRF",
            "start_date": "2026-10-26",
            "weeks": 1,
            "days": [{"name": "A", "weekday": 0}],
        },
    )
    assert response.status_code == 403
    assert (await client.get("/api/v1/plans")).json()["items"] == []


async def test_logout_revokes_session_even_if_cookie_is_replayed(client: httpx.AsyncClient) -> None:
    token = client.cookies.get("trainingos_session")
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 204
    assert (
        await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    ).status_code == 401


async def test_invalid_provider_code_creates_no_account(app: FastAPI) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as browser:
        started = await browser.get("/api/v1/auth/google/login")
        state = parse_qs(urlparse(started.headers["location"]).query)["state"][0]
        rejected = await browser.get(
            "/api/v1/auth/google/callback", params={"code": "invalid", "state": state}
        )
        assert rejected.status_code == 401
        assert (await browser.get("/api/v1/auth/me")).status_code == 401


async def test_browser_callback_redirects_with_a_committed_session(app: FastAPI) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as browser:
        started = await browser.get("/api/v1/auth/google/login")
        state = parse_qs(urlparse(started.headers["location"]).query)["state"][0]
        completed = await browser.get(
            "/api/v1/auth/google/callback",
            params={"code": "browser-user", "state": state},
            headers={"Accept": "text/html,application/xhtml+xml"},
        )
        assert completed.status_code == 303
        assert completed.headers["location"] == "http://localhost:5173"
        assert completed.headers["cache-control"] == "no-store"
        assert "trainingos_oauth_state" not in browser.cookies
        # Observe persistence after the callback request scope has committed.
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            cookies=browser.cookies,
        ) as next_request:
            assert (await next_request.get("/api/v1/auth/me")).status_code == 200
            catalog = await next_request.get("/api/v1/exercises")
            assert len(catalog.json()["items"]) == 19
