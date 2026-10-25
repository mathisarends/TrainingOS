from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import httpx
from httpx import AsyncClient


async def configured_plan(
    client: AsyncClient, *, weeks: int = 3, reps: int = 5, name: str = "Strength"
) -> dict:
    catalog = (await client.get("/api/v1/exercises")).json()["items"]
    squat = next(exercise for exercise in catalog if exercise["category"] == "squat")
    created = await client.post(
        "/api/v1/plans",
        json={
            "title": name,
            "start_date": "2026-10-26",
            "weeks": weeks,
            "days": [{"name": "A", "weekday": 0}],
        },
    )
    assert created.status_code == 201, created.text
    plan = created.json()
    plan_id, day_id = plan["id"], plan["days"][0]["id"]
    added = await client.post(
        f"/api/v1/plans/{plan_id}/days/{day_id}/slots",
        json={"exercise_id": squat["id"], "rest_seconds": 180},
    )
    assert added.status_code == 201, added.text
    slot_id = added.json()["days"][0]["slots"][0]["id"]
    effort_scale = (await client.get("/api/v1/auth/me")).json()["effort_scale"]
    prescribed = await client.put(
        f"/api/v1/plans/{plan_id}/slots/{slot_id}/weeks/1",
        json={"sets": 3, "reps": reps, "target_effort": 2 if effort_scale == "rir" else 8},
    )
    assert prescribed.status_code == 200, prescribed.text
    copied = await client.post(f"/api/v1/plans/{plan_id}/weeks/1/copy-forward")
    assert copied.status_code == 200, copied.text
    return copied.json()


async def start_training_session(client: AsyncClient, plan: dict, *, week: int = 1) -> dict:
    response = await client.post(
        "/api/v1/training-sessions",
        json={"plan_id": plan["id"], "day_id": plan["days"][0]["id"], "week": week},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def record_set(
    client: AsyncClient,
    session: dict,
    *,
    weight: Decimal | int = 100,
    reps: int = 5,
    effort: Decimal | int = 8,
) -> dict:
    response = await client.post(
        f"/api/v1/training-sessions/{session['id']}/slots/{session['slots'][0]['id']}/sets",
        json={"weight": str(weight), "reps": reps, "effort": str(effort)},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def sign_in(client: httpx.AsyncClient, subject: str = "user-a") -> dict:
    started = await client.get("/api/v1/auth/google/login")
    assert started.status_code == 307, started.text
    state = parse_qs(urlparse(started.headers["location"]).query)["state"][0]
    completed = await client.get(
        "/api/v1/auth/google/callback", params={"code": subject, "state": state}
    )
    assert completed.status_code == 200, completed.text
    return completed.json()
