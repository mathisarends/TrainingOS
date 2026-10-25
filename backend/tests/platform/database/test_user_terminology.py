import asyncio
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.features.auth.infrastructure.repository import SqlAuthRepository
from backend.features.plans.infrastructure.repository import SqlPlanRepository
from backend.features.training_sessions.infrastructure.repository import (
    SqlTrainingSessionRepository,
)
from backend.features.users.domain import EffortScale, WeightUnit
from backend.features.users.infrastructure.repository import SqlUserRepository
from backend.platform.database.migrations import migration_config

pytestmark = pytest.mark.integration


def test_rename_preserves_existing_user_training_and_template_data(database_url: str) -> None:
    """Seed the published 0001 schema independently of the new ORM, then migrate it."""
    config = migration_config()
    command.downgrade(config, "0001")
    user_id, exercise_id, plan_id, day_id, slot_id, training_session_id = (
        uuid4() for _ in range(6)
    )
    now = datetime(2026, 10, 25, 12, tzinfo=UTC)
    preferences = {
        "unit": "lb",
        "rounding_step": "5",
        "effort_scale": "rir",
        "target_weight_kg": "85",
        "timezone": "Europe/Berlin",
    }
    prescription = {"week": 1, "sets": 3, "reps": 5, "target_rpe": "8", "note": "Retain this"}
    slot = {
        "id": str(slot_id),
        "exercise_id": str(exercise_id),
        "exercise_name": "Squat",
        "category": "squat",
        "main": True,
        "rest_seconds": 180,
    }
    legacy_plan = {
        "id": str(plan_id),
        "athlete_id": str(user_id),
        "title": "Original",
        "start_date": "2026-10-25",
        "weeks": 1,
        "status": "active",
        "recommendations": True,
        "revision": 7,
        "days": [
            {
                "id": str(day_id),
                "name": "A",
                "weekday": 0,
                "slots": [slot | {"prescriptions": [prescription]}],
            }
        ],
    }
    legacy_session = {
        "plan_title": "Original",
        "day_name": "A",
        "started_at": now.isoformat(),
        "ended_at": None,
        "rest_ends_at": now.isoformat(),
        "slots": [
            slot
            | {
                "prescription": prescription,
                "skipped": False,
                "sets": [
                    {
                        "id": str(uuid4()),
                        "weight_kg": "100.25",
                        "reps": 5,
                        "rpe": "8",
                        "recorded_at": now.isoformat(),
                    }
                ],
            }
        ],
    }

    async def seed_legacy() -> None:
        engine = create_async_engine(database_url)
        try:
            async with engine.begin() as connection:
                accounts = sa.table(
                    "athletes", sa.column("id", sa.Uuid()), sa.column("preferences", sa.JSON())
                )
                await connection.execute(
                    accounts.insert().values(id=user_id, preferences=preferences)
                )
                # Each ownership table is seeded; omitted metadata fields cannot mask a lost owner.
                records = {
                    "auth_identities": {
                        "id": uuid4(),
                        "issuer": "https://accounts.google.com",
                        "subject": "legacy-user",
                    },
                    "auth_sessions": {"token_hash": "legacy-session", "expires_at": now},
                    "exercises": {
                        "id": exercise_id,
                        "name": "Squat",
                        "category": "squat",
                        "main": True,
                        "archived": False,
                    },
                    "plans": {"id": plan_id, "status": "active", "payload": legacy_plan},
                    "plan_templates": {"token_hash": "legacy-template", "payload": legacy_plan},
                    "training_sessions": {
                        "id": training_session_id,
                        "plan_id": plan_id,
                        "day_id": day_id,
                        "week": 1,
                        "started_at": now,
                        "ended_at": None,
                        "payload": legacy_session,
                    },
                    "bodyweights": {
                        "id": uuid4(),
                        "date": date(2026, 10, 25),
                        "weight_kg": Decimal("80.5"),
                    },
                }
                for name, values in records.items():
                    columns = [sa.column("athlete_id", sa.Uuid())]
                    for key, value in values.items():
                        if isinstance(value, dict):
                            column_type = sa.JSON()
                        elif key.endswith("_at"):
                            column_type = sa.DateTime(timezone=True)
                        elif key == "id" or key.endswith("_id"):
                            column_type = sa.Uuid()
                        elif isinstance(value, bool):
                            column_type = sa.Boolean()
                        elif isinstance(value, int):
                            column_type = sa.Integer()
                        elif isinstance(value, Decimal):
                            column_type = sa.Numeric(16, 8)
                        elif isinstance(value, date):
                            column_type = sa.Date()
                        else:
                            column_type = sa.String()
                        columns.append(sa.column(key, column_type))
                    table = sa.table(name, *columns)
                    await connection.execute(table.insert().values(athlete_id=user_id, **values))
        finally:
            await engine.dispose()

    async def inspect_migrated() -> None:
        engine = create_async_engine(database_url)
        try:
            async with AsyncSession(engine) as sql_session:
                user = await SqlUserRepository(sql_session).get(user_id=user_id)
                assert user is not None and user.id == user_id
                assert user.preferences.unit == WeightUnit.LB
                assert user.preferences.effort_scale == EffortScale.RIR
                assert user.preferences.rounding_step == Decimal(5)
                assert user.preferences.target_weight_kg == Decimal(85)
                plan = await SqlPlanRepository(sql_session).get(user_id=user_id, plan_id=plan_id)
                assert plan is not None and plan.user_id == user_id and plan.revision == 7
                assert plan.days[0].slots[0].id == slot_id
                assert plan.days[0].slots[0].prescriptions[0].note == "Retain this"
                template = await SqlPlanRepository(sql_session).template(
                    token_hash="legacy-template"
                )
                assert template is not None and template.user_id == user_id
                training_session = await SqlTrainingSessionRepository(sql_session).get(
                    user_id=user_id, training_session_id=training_session_id
                )
                assert training_session is not None and training_session.user_id == user_id
                assert training_session.slots[0].id == slot_id
                assert training_session.slots[0].sets[0].weight_kg == Decimal("100.25")
                assert training_session.rest_ends_at == now
                login = await SqlAuthRepository(sql_session).get_session(
                    token_hash="legacy-session"
                )
                assert login is not None and login.user_id == user_id
                for name in (
                    "auth_identities",
                    "auth_sessions",
                    "exercises",
                    "plans",
                    "plan_templates",
                    "training_sessions",
                    "bodyweights",
                ):
                    owner_table = sa.table(name, sa.column("user_id", sa.Uuid()))
                    owners = (await sql_session.exec(sa.select(owner_table.c.user_id))).all()
                    assert [row[0] for row in owners] == [user_id], name
        finally:
            await engine.dispose()

    asyncio.run(seed_legacy())
    command.upgrade(config, "head")
    command.check(config)
    asyncio.run(inspect_migrated())
    # Existing data must also survive a rollback and a second upgrade.
    command.downgrade(config, "0001")
    command.upgrade(config, "head")
    asyncio.run(inspect_migrated())
