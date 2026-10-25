"""initial training schema"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "athletes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "auth_attempts",
        sa.Column("state_hash", sa.String(), nullable=False),
        sa.Column("verifier", sa.String(), nullable=False),
        sa.Column("nonce", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("state_hash"),
    )
    op.create_index(
        op.f("ix_auth_attempts_expires_at"), "auth_attempts", ["expires_at"], unique=False
    )
    op.create_table(
        "auth_identities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("athlete_id", sa.Uuid(), nullable=False),
        sa.Column("issuer", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issuer", "subject"),
    )
    op.create_index(
        op.f("ix_auth_identities_athlete_id"), "auth_identities", ["athlete_id"], unique=False
    )
    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("athlete_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_auth_sessions_athlete_id"), "auth_sessions", ["athlete_id"], unique=False
    )
    op.create_index(
        op.f("ix_auth_sessions_expires_at"), "auth_sessions", ["expires_at"], unique=False
    )
    op.create_table(
        "bodyweights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("athlete_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=16, scale=8), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("athlete_id", "date"),
    )
    op.create_index(op.f("ix_bodyweights_athlete_id"), "bodyweights", ["athlete_id"], unique=False)
    op.create_table(
        "exercises",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("athlete_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("main", sa.Boolean(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exercises_athlete_id"), "exercises", ["athlete_id"], unique=False)
    op.create_table(
        "plan_templates",
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("athlete_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_plan_templates_athlete_id"), "plan_templates", ["athlete_id"], unique=False
    )
    op.create_table(
        "plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("athlete_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plans_athlete_id"), "plans", ["athlete_id"], unique=False)
    op.create_index(
        "uq_active_plan",
        "plans",
        ["athlete_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "training_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("athlete_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("day_id", sa.Uuid(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("athlete_id", "plan_id", "day_id", "week"),
    )
    op.create_index(
        op.f("ix_training_sessions_athlete_id"), "training_sessions", ["athlete_id"], unique=False
    )
    op.create_index(
        op.f("ix_training_sessions_plan_id"), "training_sessions", ["plan_id"], unique=False
    )
    op.create_index(
        "uq_running_session",
        "training_sessions",
        ["athlete_id"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
        sqlite_where=sa.text("ended_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_running_session",
        table_name="training_sessions",
        postgresql_where=sa.text("ended_at IS NULL"),
        sqlite_where=sa.text("ended_at IS NULL"),
    )
    op.drop_index(op.f("ix_training_sessions_plan_id"), table_name="training_sessions")
    op.drop_index(op.f("ix_training_sessions_athlete_id"), table_name="training_sessions")
    op.drop_table("training_sessions")
    op.drop_index(
        "uq_active_plan",
        table_name="plans",
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )
    op.drop_index(op.f("ix_plans_athlete_id"), table_name="plans")
    op.drop_table("plans")
    op.drop_index(op.f("ix_plan_templates_athlete_id"), table_name="plan_templates")
    op.drop_table("plan_templates")
    op.drop_index(op.f("ix_exercises_athlete_id"), table_name="exercises")
    op.drop_table("exercises")
    op.drop_index(op.f("ix_bodyweights_athlete_id"), table_name="bodyweights")
    op.drop_table("bodyweights")
    op.drop_index(op.f("ix_auth_sessions_expires_at"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_athlete_id"), table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index(op.f("ix_auth_identities_athlete_id"), table_name="auth_identities")
    op.drop_table("auth_identities")
    op.drop_index(op.f("ix_auth_attempts_expires_at"), table_name="auth_attempts")
    op.drop_table("auth_attempts")
    op.drop_table("athletes")
