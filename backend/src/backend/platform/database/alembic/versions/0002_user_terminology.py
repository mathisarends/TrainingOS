"""Rename athletes to users without replacing existing account or training data."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNED_TABLES = (
    "auth_identities",
    "auth_sessions",
    "exercises",
    "plans",
    "plan_templates",
    "training_sessions",
    "bodyweights",
)


def rename_payload_owner(*, old_key: str, new_key: str) -> None:
    connection = op.get_bind()
    for name, primary_key, key_type in (
        ("plans", "id", sa.Uuid()),
        ("plan_templates", "token_hash", sa.String()),
    ):
        table = sa.table(name, sa.column(primary_key, key_type), sa.column("payload", sa.JSON()))
        rows = connection.execute(sa.select(table.c[primary_key], table.c.payload)).all()
        for identifier, payload in rows:
            updated = dict(payload)
            updated[new_key] = updated.pop(old_key)
            connection.execute(
                table.update().where(table.c[primary_key] == identifier).values(payload=updated)
            )


def rename_owner_columns(*, old_key: str, new_key: str) -> None:
    for table in OWNED_TABLES:
        op.drop_index(f"ix_{table}_{old_key}", table_name=table)
        op.alter_column(
            table,
            old_key,
            new_column_name=new_key,
            existing_type=sa.Uuid(),
            existing_nullable=False,
        )
        op.create_index(f"ix_{table}_{new_key}", table, [new_key])


def running_session_index(*, old_name: str, new_name: str, owner_key: str) -> None:
    op.drop_index(old_name, table_name="training_sessions")
    op.create_index(
        new_name,
        "training_sessions",
        [owner_key],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
        sqlite_where=sa.text("ended_at IS NULL"),
    )


def upgrade() -> None:
    op.rename_table("athletes", "users")
    rename_owner_columns(old_key="athlete_id", new_key="user_id")
    rename_payload_owner(old_key="athlete_id", new_key="user_id")
    running_session_index(
        old_name="uq_running_session", new_name="uq_running_training_session", owner_key="user_id"
    )


def downgrade() -> None:
    running_session_index(
        old_name="uq_running_training_session", new_name="uq_running_session", owner_key="user_id"
    )
    rename_payload_owner(old_key="user_id", new_key="athlete_id")
    rename_owner_columns(old_key="user_id", new_key="athlete_id")
    op.rename_table("users", "athletes")
