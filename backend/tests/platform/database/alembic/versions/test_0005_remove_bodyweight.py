import asyncio
from datetime import date
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from backend.platform.database.migrations import migration_config
from tests.support import configured_plan, record_set, start_training_session

pytestmark = pytest.mark.integration


async def test_migration_removes_measurements_and_target_but_preserves_training(
    client: AsyncClient,
    database_url: str,
) -> None:
    plan = await configured_plan(client)
    session = await start_training_session(client, plan)
    await record_set(client, session)
    user_id = UUID((await client.get("/api/v1/auth/me")).json()["id"])
    before = (await client.get(f"/api/v1/training-sessions/{session['id']}")).json()
    config = migration_config()
    await asyncio.to_thread(command.downgrade, config, "0004")
    engine = create_async_engine(database_url)
    users = sa.table("users", sa.column("id", sa.Uuid()), sa.column("preferences", sa.JSON()))
    weights = sa.table(
        "bodyweights",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("date", sa.Date()),
        sa.column("weight_kg", sa.Numeric(16, 8)),
    )
    try:
        async with engine.begin() as connection:
            preferences = await connection.scalar(
                sa.select(users.c.preferences).where(users.c.id == user_id)
            )
            await connection.execute(
                users.update()
                .where(users.c.id == user_id)
                .values(preferences=preferences | {"target_weight_kg": "85"})
            )
            await connection.execute(
                weights.insert().values(
                    id=uuid4(), user_id=user_id, date=date(2026, 10, 29), weight_kg=80
                )
            )
        await asyncio.to_thread(command.upgrade, config, "head")
        await asyncio.to_thread(command.check, config)
        # Inspect committed data from a new database scope after migration closes.
        async with engine.connect() as connection:
            names = await connection.run_sync(lambda conn: sa.inspect(conn).get_table_names())
            assert "bodyweights" not in names
            preferences = await connection.scalar(
                sa.select(users.c.preferences).where(users.c.id == user_id)
            )
            assert "target_weight_kg" not in preferences
            assert preferences["unit"] == "kg"
    finally:
        await engine.dispose()
    after = (await client.get(f"/api/v1/training-sessions/{session['id']}")).json()
    assert after["slots"] == before["slots"]
    assert (await client.get(f"/api/v1/plans/{plan['id']}")).json()["id"] == plan["id"]
    exported = (await client.get("/api/v1/users/me/export")).json()
    assert exported["format_version"] == 3
    assert "bodyweight" not in exported and "target_weight" not in exported["user"]


async def test_removed_bodyweight_contracts_are_unavailable(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/bodyweight")).status_code == 404
    assert (
        await client.put("/api/v1/bodyweight", json={"date": "2026-10-29", "weight": 80})
    ).status_code == 404
    assert (
        await client.put("/api/v1/users/me/preferences", json={"target_weight": 85})
    ).status_code == 422
    schema = (await client.get("/openapi.json")).json()
    assert not any("bodyweight" in path for path in schema["paths"])
