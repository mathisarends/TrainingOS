from decimal import Decimal as D

import pytest
from httpx import AsyncClient

from tests.support import configured_plan, record_set, start_training_session

pytestmark = pytest.mark.integration


async def test_exercise_with_history_is_archived_and_keeps_records(client: AsyncClient) -> None:
    plan = await configured_plan(client)
    session = await start_training_session(client, plan)
    await record_set(client, session)
    exercise_id = session["slots"][0]["exercise_id"]

    deleted = await client.delete(f"/api/v1/exercises/{exercise_id}")
    assert deleted.status_code == 204
    catalog = (await client.get("/api/v1/exercises")).json()["items"]
    assert next(item for item in catalog if item["id"] == exercise_id)["archived"]
    reloaded = (await client.get(f"/api/v1/training-sessions/{session['id']}")).json()
    assert reloaded["slots"][0]["exercise_id"] == exercise_id
    assert D(reloaded["slots"][0]["sets"][0]["e1rm"]) == 125


async def test_catalog_changes_update_plan_and_leave_session_snapshot_intact(
    client: AsyncClient,
) -> None:
    plan = await configured_plan(client)
    session = await start_training_session(client, plan)
    slot = session["slots"][0]

    renamed = await client.put(
        f"/api/v1/exercises/{slot['exercise_id']}",
        json={"name": "Squat renamed", "category": "legs", "main": False},
    )
    assert renamed.status_code == 200
    current_plan = (await client.get(f"/api/v1/plans/{plan['id']}")).json()
    current_session = (await client.get(f"/api/v1/training-sessions/{session['id']}")).json()
    assert current_plan["days"][0]["slots"][0]["exercise_name"] == "Squat renamed"
    assert current_plan["days"][0]["slots"][0]["category"] == "legs"
    assert current_session["slots"][0]["exercise_name"] == slot["exercise_name"]
    feedback = await record_set(client, session)
    assert not feedback["new_personal_record"]


async def test_custom_exercise_without_references_can_be_deleted(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/exercises", json={"name": "Cable curl", "category": "biceps", "main": False}
    )
    assert created.status_code == 201
    exercise_id = created.json()["id"]
    assert (await client.delete(f"/api/v1/exercises/{exercise_id}")).status_code == 204
    assert all(
        item["id"] != exercise_id
        for item in (await client.get("/api/v1/exercises")).json()["items"]
    )


async def test_captured_exercise_is_retained_before_first_set(client: AsyncClient) -> None:
    plan = await configured_plan(client)
    session = await start_training_session(client, plan)
    slot = session["slots"][0]
    await client.delete(f"/api/v1/plans/{plan['id']}/days/{session['day_id']}/slots/{slot['id']}")
    assert (await client.delete(f"/api/v1/exercises/{slot['exercise_id']}")).status_code == 204
    feedback = await record_set(client, session)
    assert feedback["new_personal_record"]
    reloaded = (await client.get(f"/api/v1/training-sessions/{session['id']}")).json()
    assert len(reloaded["slots"][0]["sets"]) == 1
