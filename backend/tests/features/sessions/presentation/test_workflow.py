from datetime import datetime, timedelta
from decimal import Decimal as D

import pytest
from httpx import AsyncClient

from tests.support import configured_plan, record_set, start_session

pytestmark = pytest.mark.integration


async def test_training_correction_recomputes_records_and_volume(client: AsyncClient) -> None:
    plan = await configured_plan(client)
    session = await start_session(client, plan)
    first = await record_set(client, session)
    assert first["new_personal_record"]
    assert D(first["work_set"]["e1rm"]) == D(125)
    assert D(first["backoff_weight"]) == D("102.5")
    assert first["session"]["rest_remaining_seconds"] == 180
    assert (await client.post(f"/api/v1/sessions/{session['id']}/finish")).status_code == 200
    statistics = (await client.get("/api/v1/statistics")).json()
    assert D(statistics["tonnage"]) == D(500)
    assert statistics["work_sets"] == 1
    assert len(statistics["durations"]) == 1
    set_id, slot_id = first["work_set"]["id"], session["slots"][0]["id"]
    corrected = await client.put(
        f"/api/v1/sessions/{session['id']}/slots/{slot_id}/sets/{set_id}",
        json={"weight": 80, "reps": 5, "effort": 8},
    )
    assert corrected.status_code == 200, corrected.text
    statistics = (await client.get("/api/v1/statistics")).json()
    assert D(statistics["tonnage"]) == D(400)
    assert D(statistics["records"][0]["e1rm"]) == D(100)
    deleted = await client.delete(f"/api/v1/sessions/{session['id']}/slots/{slot_id}/sets/{set_id}")
    assert deleted.status_code == 200
    assert (await client.get("/api/v1/statistics")).json()["records"] == []


async def test_timer_deadline_persists_and_adjusts_across_requests(client: AsyncClient) -> None:
    session = await start_session(client, await configured_plan(client))
    recorded = await record_set(client, session)
    deadline = recorded["session"]["rest_ends_at"]
    reloaded = (await client.get(f"/api/v1/sessions/{session['id']}")).json()
    assert reloaded["rest_ends_at"] == deadline
    extended = (
        await client.put(f"/api/v1/sessions/{session['id']}/timer", json={"delta_seconds": 30})
    ).json()
    assert datetime.fromisoformat(extended["rest_ends_at"]) == datetime.fromisoformat(
        deadline
    ) + timedelta(seconds=30)
    shortened = (
        await client.put(f"/api/v1/sessions/{session['id']}/timer", json={"delta_seconds": -60})
    ).json()
    assert datetime.fromisoformat(shortened["rest_ends_at"]) == datetime.fromisoformat(
        deadline
    ) - timedelta(seconds=30)
    skipped = (await client.put(f"/api/v1/sessions/{session['id']}/timer", json={})).json()
    assert skipped["rest_ends_at"] is None


async def test_recommendation_matches_slot_and_prescription_reps(client: AsyncClient) -> None:
    plan = await configured_plan(client)
    first = await start_session(client, plan)
    slot_id = first["slots"][0]["id"]
    empty = (await client.get(f"/api/v1/sessions/{first['id']}/slots/{slot_id}/guidance")).json()
    assert empty["recommended_weight"] is None
    await record_set(client, first)
    await client.post(f"/api/v1/sessions/{first['id']}/finish")
    second = await start_session(client, plan, week=2)
    guidance = (
        await client.get(f"/api/v1/sessions/{second['id']}/slots/{slot_id}/guidance")
    ).json()
    assert D(guidance["recommended_weight"]) == D("102.5")
    assert len(guidance["last_sets"]) == 1
    assert second["slots"][0]["sets"] == []
    await client.put(
        f"/api/v1/plans/{plan['id']}",
        json={"title": plan["title"], "start_date": plan["start_date"], "recommendations": False},
    )
    assert (await client.get(f"/api/v1/sessions/{second['id']}/slots/{slot_id}/guidance")).json()[
        "recommended_weight"
    ] is None


async def test_session_snapshot_survives_slot_and_plan_deletion(client: AsyncClient) -> None:
    plan = await configured_plan(client)
    session = await start_session(client, plan)
    await record_set(client, session)
    slot_id = session["slots"][0]["id"]
    await client.delete(f"/api/v1/plans/{plan['id']}/days/{session['day_id']}/slots/{slot_id}")
    await client.delete(f"/api/v1/plans/{plan['id']}")
    reloaded = (await client.get(f"/api/v1/sessions/{session['id']}")).json()
    assert reloaded["slots"][0]["id"] == slot_id
    assert D(reloaded["slots"][0]["sets"][0]["weight"]) == 100
    assert D((await client.get("/api/v1/statistics")).json()["tonnage"]) == 500


async def test_rir_and_lb_settings_preserve_stored_history(client: AsyncClient) -> None:
    configured = await client.put(
        "/api/v1/athlete/preferences",
        json={"unit": "lb", "rounding_step": 5, "effort_scale": "rir"},
    )
    assert configured.status_code == 200
    plan = await configured_plan(client)
    session = await start_session(client, plan)
    feedback = await record_set(client, session, weight=220, effort=2)
    assert D(feedback["work_set"]["rpe"]) == 8
    assert D(feedback["work_set"]["e1rm"]) == 275
    await client.put(
        "/api/v1/athlete/preferences",
        json={"unit": "kg", "rounding_step": "2.5", "effort_scale": "rpe"},
    )
    reloaded = (await client.get(f"/api/v1/sessions/{session['id']}")).json()
    assert D(reloaded["slots"][0]["sets"][0]["weight"]) == D("99.79032140")
    assert D(reloaded["slots"][0]["sets"][0]["effort"]) == 8
