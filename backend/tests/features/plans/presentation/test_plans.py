from decimal import Decimal as D

import pytest
from httpx import AsyncClient

from tests.support import configured_plan, start_session

pytestmark = pytest.mark.integration


async def test_progression_preview_is_not_saved_and_apply_checks_revision(
    client: AsyncClient,
) -> None:
    plan = await configured_plan(client, weeks=4)
    plan_id = plan["id"]
    preview = await client.post(
        f"/api/v1/plans/{plan_id}/progression/preview", json={"increment": "0.5", "deload": True}
    )
    assert preview.status_code == 200, preview.text
    current = (await client.get(f"/api/v1/plans/{plan_id}")).json()
    assert current == plan
    prescriptions = preview.json()["plan"]["days"][0]["slots"][0]["prescriptions"]
    assert [D(p["target_rpe"]) for p in prescriptions] == [D(8), D("8.5"), D(9), D(6)]
    assert prescriptions[-1]["sets"] == 2

    await client.put(
        f"/api/v1/plans/{plan_id}",
        json={"title": "Revised", "start_date": plan["start_date"], "recommendations": True},
    )
    stale = await client.post(
        f"/api/v1/plans/{plan_id}/progression/apply",
        json={
            "increment": "0.5",
            "deload": True,
            "expected_revision": preview.json()["base_revision"],
        },
    )
    assert stale.status_code == 409
    fresh = (
        await client.post(
            f"/api/v1/plans/{plan_id}/progression/preview",
            json={"increment": "0.5", "deload": True},
        )
    ).json()
    applied = await client.post(
        f"/api/v1/plans/{plan_id}/progression/apply",
        json={"increment": "0.5", "deload": True, "expected_revision": fresh["base_revision"]},
    )
    assert applied.status_code == 200
    assert (await client.get(f"/api/v1/plans/{plan_id}")).json() == applied.json()


async def test_activating_another_plan_ends_previous_and_selects_next_day(
    client: AsyncClient,
) -> None:
    first = await configured_plan(client)
    second = await configured_plan(client, name="Next")
    await client.put(f"/api/v1/plans/{first['id']}/status", json={"status": "active"})
    await client.put(f"/api/v1/plans/{second['id']}/status", json={"status": "active"})
    plans = (await client.get("/api/v1/plans")).json()["items"]
    assert next(plan for plan in plans if plan["id"] == first["id"])["status"] == "ended"
    assert sum(plan["status"] == "active" for plan in plans) == 1
    training = (await client.get("/api/v1/plans/next-training")).json()
    assert training["plan_id"] == second["id"]
    assert training["week"] == 1
    assert training["scheduled_date"] == "2026-10-26"
    session = await start_session(client, second)
    assert (await client.get("/api/v1/plans/next-training")).json()[
        "running_session_id"
    ] == session["id"]
    await client.post(f"/api/v1/sessions/{session['id']}/finish")
    assert (await client.get("/api/v1/plans/next-training")).json()["week"] == 2


async def test_template_import_is_an_independent_copy_without_sessions(
    client: AsyncClient, other_client: AsyncClient
) -> None:
    original = await configured_plan(client)
    await start_session(client, original)
    share = (await client.post(f"/api/v1/plans/{original['id']}/shares")).json()["token"]
    imported = await other_client.post(
        f"/api/v1/templates/{share}/import", json={"title": "Mine", "start_date": "2026-11-02"}
    )
    assert imported.status_code == 201, imported.text
    copied = imported.json()
    assert copied["id"] != original["id"]
    assert copied["days"][0]["id"] != original["days"][0]["id"]
    assert copied["days"][0]["slots"][0]["id"] != original["days"][0]["slots"][0]["id"]
    assert (
        copied["days"][0]["slots"][0]["exercise_id"]
        != original["days"][0]["slots"][0]["exercise_id"]
    )
    assert (await other_client.get("/api/v1/sessions")).json()["items"] == []
    await client.delete(f"/api/v1/plans/{original['id']}")
    await client.delete(f"/api/v1/templates/{share}")
    assert (await other_client.get(f"/api/v1/plans/{copied['id']}")).json() == copied
    assert (
        await other_client.post(
            f"/api/v1/templates/{share}/import", json={"title": "Again", "start_date": "2026-11-02"}
        )
    ).status_code == 404


async def test_duplicate_has_new_slot_identity_and_no_performance_history(
    client: AsyncClient,
) -> None:
    original = await configured_plan(client)
    copied = await client.post(
        f"/api/v1/plans/{original['id']}/duplicate",
        json={"title": "Next block", "start_date": "2026-11-16"},
    )
    assert copied.status_code == 201
    assert copied.json()["days"][0]["slots"][0]["id"] != original["days"][0]["slots"][0]["id"]
    assert (
        copied.json()["days"][0]["slots"][0]["prescriptions"]
        == original["days"][0]["slots"][0]["prescriptions"]
    )
