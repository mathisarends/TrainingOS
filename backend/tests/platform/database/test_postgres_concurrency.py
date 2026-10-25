import asyncio
import os

import pytest
from httpx import AsyncClient

from tests.support import configured_plan, start_training_session

pytestmark = [
    pytest.mark.integration,
    pytest.mark.postgres,
    pytest.mark.skipif(
        not os.environ.get("TRAININGOS_TEST_POSTGRES_URL"),
        reason="Requires the dedicated PostgreSQL test URL",
    ),
]


async def test_concurrent_plan_activation_leaves_exactly_one_active(client: AsyncClient) -> None:
    first, second = await configured_plan(client), await configured_plan(client, name="Other")
    responses = await asyncio.wait_for(
        asyncio.gather(
            client.put(f"/api/v1/plans/{first['id']}/status", json={"status": "active"}),
            client.put(f"/api/v1/plans/{second['id']}/status", json={"status": "active"}),
        ),
        timeout=10,
    )
    assert [response.status_code for response in responses] == [200, 200]
    plans = (await client.get("/api/v1/plans")).json()["items"]
    assert sorted(plan["status"] for plan in plans) == ["active", "ended"]


async def test_concurrent_set_recording_does_not_lose_a_set(client: AsyncClient) -> None:
    session = await start_training_session(client, await configured_plan(client))
    path = f"/api/v1/training-sessions/{session['id']}/slots/{session['slots'][0]['id']}/sets"
    responses = await asyncio.wait_for(
        asyncio.gather(
            client.post(path, json={"weight": 100, "reps": 5, "effort": 8}),
            client.post(path, json={"weight": 90, "reps": 5, "effort": 8}),
        ),
        timeout=10,
    )
    assert [response.status_code for response in responses] == [201, 201]
    reloaded = (await client.get(f"/api/v1/training-sessions/{session['id']}")).json()
    assert len(reloaded["slots"][0]["sets"]) == 2


async def test_concurrent_session_starts_are_serialized(client: AsyncClient) -> None:
    plan = await configured_plan(client)
    body = {"plan_id": plan["id"], "day_id": plan["days"][0]["id"], "week": 1}
    responses = await asyncio.wait_for(
        asyncio.gather(
            client.post("/api/v1/training-sessions", json=body),
            client.post("/api/v1/training-sessions", json=body),
        ),
        timeout=10,
    )
    assert sorted(response.status_code for response in responses) == [201, 409]
    assert len((await client.get("/api/v1/training-sessions")).json()["items"]) == 1
