from decimal import Decimal as D

import pytest
from httpx import AsyncClient

from tests.support import configured_plan, record_set, start_session

pytestmark = pytest.mark.integration


async def test_reordering_does_not_move_history_between_slots(client: AsyncClient) -> None:
    plan = await configured_plan(client)
    day_id = plan["days"][0]["id"]
    squat_slot = plan["days"][0]["slots"][0]["id"]
    bench = next(
        exercise
        for exercise in (await client.get("/api/v1/exercises")).json()["items"]
        if exercise["category"] == "bench_press"
    )
    added = (
        await client.post(
            f"/api/v1/plans/{plan['id']}/days/{day_id}/slots", json={"exercise_id": bench["id"]}
        )
    ).json()
    bench_slot = added["days"][0]["slots"][1]["id"]
    await client.put(
        f"/api/v1/plans/{plan['id']}/slots/{bench_slot}/weeks/1",
        json={"sets": 3, "reps": 5, "target_effort": 8},
    )
    await client.post(f"/api/v1/plans/{plan['id']}/weeks/1/copy-forward")
    first = await start_session(client, plan)
    await record_set(client, first, weight=100)
    bench_feedback = await client.post(
        f"/api/v1/sessions/{first['id']}/slots/{bench_slot}/sets",
        json={"weight": 60, "reps": 5, "effort": 8},
    )
    assert bench_feedback.status_code == 201
    await client.post(f"/api/v1/sessions/{first['id']}/finish")

    reordered = await client.put(
        f"/api/v1/plans/{plan['id']}/days/{day_id}/slot-order",
        json={"slot_ids": [bench_slot, squat_slot]},
    )
    assert reordered.status_code == 200
    second = await start_session(client, plan, week=2)
    assert [slot["id"] for slot in second["slots"]] == [bench_slot, squat_slot]
    bench_guidance = (
        await client.get(f"/api/v1/sessions/{second['id']}/slots/{bench_slot}/guidance")
    ).json()
    squat_guidance = (
        await client.get(f"/api/v1/sessions/{second['id']}/slots/{squat_slot}/guidance")
    ).json()
    assert D(bench_guidance["last_sets"][0]["weight"]) == 60
    assert D(squat_guidance["last_sets"][0]["weight"]) == 100
    original = (await client.get(f"/api/v1/sessions/{first['id']}")).json()
    assert [slot["id"] for slot in original["slots"]] == [squat_slot, bench_slot]


async def test_recommendation_skips_recent_week_with_different_prescribed_reps(
    client: AsyncClient,
) -> None:
    plan = await configured_plan(client)
    slot_id = plan["days"][0]["slots"][0]["id"]
    first = await start_session(client, plan)
    await record_set(client, first, weight=100)
    await client.post(f"/api/v1/sessions/{first['id']}/finish")
    await client.put(
        f"/api/v1/plans/{plan['id']}/slots/{slot_id}/weeks/2",
        json={"sets": 3, "reps": 8, "target_effort": 8},
    )
    second = await start_session(client, plan, week=2)
    no_match = (
        await client.get(f"/api/v1/sessions/{second['id']}/slots/{slot_id}/guidance")
    ).json()
    assert no_match["recommended_weight"] is None
    assert len(no_match["last_sets"]) == 1
    await record_set(client, second, weight=150, reps=8)
    await client.post(f"/api/v1/sessions/{second['id']}/finish")
    third = await start_session(client, plan, week=3)
    guidance = (await client.get(f"/api/v1/sessions/{third['id']}/slots/{slot_id}/guidance")).json()
    assert D(guidance["recommended_weight"]) == D("102.5")
    assert D(guidance["last_sets"][0]["weight"]) == 150
