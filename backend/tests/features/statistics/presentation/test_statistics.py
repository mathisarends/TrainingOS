from decimal import Decimal as D

import pytest
from httpx import AsyncClient

from tests.support import configured_plan, record_set, start_session

pytestmark = pytest.mark.integration


async def test_plan_comparison_and_record_history_recompute_after_correction(
    client: AsyncClient,
) -> None:
    first = await configured_plan(client, name="First")
    session_a = await start_session(client, first)
    await record_set(client, session_a, weight=100)
    await client.post(f"/api/v1/sessions/{session_a['id']}/finish")
    second = await configured_plan(client, name="Second")
    session_b = await start_session(client, second)
    feedback = await record_set(client, session_b, weight=120)
    await client.post(f"/api/v1/sessions/{session_b['id']}/finish")
    first_times = await client.put(
        f"/api/v1/sessions/{session_a['id']}/times",
        json={
            "started_at": "2026-01-01T23:45:00Z",
            "ended_at": "2026-01-01T23:46:00Z",
        },
    )
    second_times = await client.put(
        f"/api/v1/sessions/{session_b['id']}/times",
        json={
            "started_at": "2026-01-02T00:30:00Z",
            "ended_at": "2026-01-02T00:31:00Z",
        },
    )
    assert first_times.status_code == second_times.status_code == 200

    comparison = (
        await client.get(
            "/api/v1/statistics/comparison",
            params={"first_plan_id": first["id"], "second_plan_id": second["id"]},
        )
    ).json()
    assert D(comparison["first"]["tonnage"]) == 500
    assert D(comparison["second"]["tonnage"]) == 600
    assert comparison["first"]["weekly_volume"][0]["category"] == "squat"
    assert comparison["first"]["weekly_volume"][0]["work_sets"] == 1
    statistics = (await client.get("/api/v1/statistics")).json()
    assert [D(point["e1rm"]) for point in statistics["records"]] == [D(125), D(150)]
    assert len(statistics["strength"]) == 2
    assert statistics["activity_dates"] == ["2026-01-02"]
    corrected = await client.put(
        f"/api/v1/sessions/{session_b['id']}/slots/{session_b['slots'][0]['id']}/sets/{feedback['work_set']['id']}",
        json={"weight": 80, "reps": 5, "effort": 8},
    )
    assert corrected.status_code == 200
    statistics = (await client.get("/api/v1/statistics")).json()
    assert [D(point["e1rm"]) for point in statistics["records"]] == [D(125)]
    assert D(statistics["tonnage"]) == 900
