from decimal import Decimal as D

import pytest
from httpx import AsyncClient
from sqlalchemy import func
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select

from tests.support import configured_plan, record_set, sign_in, start_training_session

pytestmark = pytest.mark.integration


async def test_owned_resources_are_hidden_from_another_user(
    client: AsyncClient, other_client: AsyncClient
) -> None:
    plan = await configured_plan(client)
    session = await start_training_session(client, plan)
    await record_set(client, session)
    await client.put("/api/v1/bodyweight", json={"date": "2026-10-25", "weight": 80})

    assert (await other_client.get(f"/api/v1/plans/{plan['id']}")).status_code == 404
    assert (await other_client.delete(f"/api/v1/plans/{plan['id']}")).status_code == 404
    assert (await other_client.get(f"/api/v1/training-sessions/{session['id']}")).status_code == 404
    denied = await other_client.post(
        f"/api/v1/training-sessions/{session['id']}/slots/{session['slots'][0]['id']}/sets",
        json={"weight": 200, "reps": 5, "effort": 8},
    )
    assert denied.status_code == 404
    assert (await other_client.get("/api/v1/plans")).json()["items"] == []
    assert (await other_client.get("/api/v1/training-sessions")).json()["items"] == []
    assert (await other_client.get("/api/v1/bodyweight")).json()["items"] == []
    assert (await other_client.get("/api/v1/users/me/export")).json()["training_sessions"] == []
    assert (
        len(
            (await client.get(f"/api/v1/training-sessions/{session['id']}")).json()["slots"][0][
                "sets"
            ]
        )
        == 1
    )


async def test_export_contains_owned_training_and_identity_data_without_credentials(
    client: AsyncClient,
) -> None:
    plan = await configured_plan(client)
    session = await start_training_session(client, plan)
    await record_set(client, session)
    await client.put("/api/v1/bodyweight", json={"date": "2026-10-25", "weight": 80})
    await client.post(f"/api/v1/plans/{plan['id']}/shares")

    response = await client.get("/api/v1/users/me/export")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    exported = response.json()
    assert exported["format_version"] == 2
    assert exported["plans"][0]["id"] == plan["id"]
    assert exported["training_sessions"][0]["id"] == session["id"]
    assert D(exported["bodyweight"][0]["weight"]) == 80
    assert len(exported["shared_templates"]) == 1
    assert exported["identities"] == [
        {"issuer": "https://accounts.google.com", "subject": "user-a"}
    ]
    assert client.cookies.get("trainingos_session") not in response.text


async def test_account_delete_cascades_all_owned_rows_and_revokes_login(
    client: AsyncClient, database_url: str
) -> None:
    original_id = (await client.get("/api/v1/auth/me")).json()["id"]
    plan = await configured_plan(client)
    session = await start_training_session(client, plan)
    await record_set(client, session)
    await client.put("/api/v1/bodyweight", json={"date": "2026-10-25", "weight": 80})
    await client.post(f"/api/v1/plans/{plan['id']}/shares")
    token = client.cookies.get("trainingos_session")

    response = await client.delete("/api/v1/users/me")
    assert response.status_code == 204
    assert (
        await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    ).status_code == 401
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as connection:
            for table in SQLModel.metadata.sorted_tables:
                if table.name != "auth_attempts":
                    count = await connection.scalar(select(func.count()).select_from(table))
                    assert count == 0, table.name
    finally:
        await engine.dispose()
    new_account = await sign_in(client)
    assert new_account["id"] != original_id
