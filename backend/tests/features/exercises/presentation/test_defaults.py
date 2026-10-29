from decimal import Decimal as D

import pytest
from httpx import AsyncClient

from tests.support import configured_plan, start_training_session

pytestmark = pytest.mark.integration
URL = "/api/v1/exercises/category-defaults"


async def test_defaults_persist_across_requests_are_owned_and_exported(
    client: AsyncClient, other_client: AsyncClient
) -> None:
    initial = (await client.get(URL)).json()["items"]
    assert len(initial) == 10
    squat = next(item for item in initial if item["category"] == "squat")
    assert (squat["rest_seconds"], squat["sets"], squat["reps"], D(squat["target_rpe"])) == (
        240,
        3,
        7,
        D("7.5"),
    )
    request = {"rest_seconds": 300, "sets": 5, "reps": 4, "target_effort": "9"}
    saved = await client.put(f"{URL}/squat", json=request)
    assert saved.status_code == 200, saved.text
    # Each HTTP call closes its producing function scope before the next read.
    reloaded = (await client.get(URL)).json()["items"]
    persisted = next(item for item in reloaded if item["category"] == "squat")
    assert persisted | {
        "target_rpe": D(persisted["target_rpe"]),
        "target_effort": D(persisted["target_effort"]),
    } == saved.json() | {"target_rpe": D("9"), "target_effort": D("9")}
    other = (await other_client.get(URL)).json()["items"]
    assert next(item for item in other if item["category"] == "squat") == squat
    exported = (await client.get("/api/v1/users/me/export")).json()
    assert exported["category_defaults"] == reloaded


async def test_defaults_convert_rir_and_invalid_updates_leave_saved_values_intact(
    client: AsyncClient,
) -> None:
    changed = await client.put(
        "/api/v1/users/me/preferences",
        json={
            "unit": "kg",
            "rounding_step": "2.5",
            "effort_scale": "rir",
            "timezone": "Europe/Berlin",
        },
    )
    assert changed.status_code == 200, changed.text
    saved = await client.put(
        f"{URL}/back", json={"rest_seconds": 150, "sets": 4, "reps": 10, "target_effort": "1.5"}
    )
    assert saved.status_code == 200, saved.text
    assert D(saved.json()["target_rpe"]) == D("8.5")
    assert D(saved.json()["target_effort"]) == D("1.5")
    for update in [
        {"sets": 0},
        {"rest_seconds": 3601},
        {"target_effort": "0.1"},
        {"target_effort": "10"},
    ]:
        response = await client.put(
            f"{URL}/back",
            json={"rest_seconds": 150, "sets": 4, "reps": 10, "target_effort": "1.5", **update},
        )
        assert response.status_code == 422, response.text
    current = (await client.get(URL)).json()["items"]
    assert next(item for item in current if item["category"] == "back") == saved.json()


async def test_new_slots_use_defaults_without_rewriting_existing_plans_or_snapshots(
    client: AsyncClient,
) -> None:
    plan = await configured_plan(client)
    session = await start_training_session(client, plan)
    old_slot = plan["days"][0]["slots"][0]
    changed = await client.put(
        f"{URL}/squat", json={"rest_seconds": 270, "sets": 4, "reps": 6, "target_effort": "8.5"}
    )
    assert changed.status_code == 200, changed.text
    assert (await client.get(f"/api/v1/plans/{plan['id']}")).json() == plan
    reloaded_session = (await client.get(f"/api/v1/training-sessions/{session['id']}")).json()
    assert reloaded_session["slots"] == session["slots"]
    url = f"/api/v1/plans/{plan['id']}/days/{plan['days'][0]['id']}/slots"
    added = await client.post(url, json={"exercise_id": old_slot["exercise_id"]})
    assert added.status_code == 201, added.text
    reloaded_plan = (await client.get(f"/api/v1/plans/{plan['id']}")).json()
    slots = reloaded_plan["days"][0]["slots"]
    assert slots[0] == old_slot
    assert slots[1]["rest_seconds"] == 270
    assert [item["week"] for item in slots[1]["prescriptions"]] == list(range(1, plan["weeks"] + 1))
    assert all(
        (item["sets"], item["reps"], D(item["target_rpe"])) == (4, 6, D("8.5"))
        for item in slots[1]["prescriptions"]
    )
    overridden = await client.post(
        url, json={"exercise_id": old_slot["exercise_id"], "rest_seconds": 0}
    )
    assert overridden.status_code == 201, overridden.text
    assert overridden.json()["days"][0]["slots"][-1]["rest_seconds"] == 0
