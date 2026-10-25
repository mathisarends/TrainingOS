"""Relational ownership/indexes; plan and session contents are aggregate snapshots."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, Column, DateTime, Index, Numeric, String, UniqueConstraint, text
from sqlmodel import Field, SQLModel


class AthleteRow(SQLModel, table=True):
    __tablename__ = "athletes"
    id: UUID = Field(primary_key=True)
    preferences: dict[str, str | None] = Field(sa_column=Column(JSON, nullable=False))


class IdentityRow(SQLModel, table=True):
    __tablename__ = "auth_identities"
    __table_args__ = (UniqueConstraint("issuer", "subject"),)
    id: UUID = Field(primary_key=True)
    athlete_id: UUID = Field(foreign_key="athletes.id", ondelete="CASCADE", index=True)
    issuer: str
    subject: str


class AttemptRow(SQLModel, table=True):
    __tablename__ = "auth_attempts"
    state_hash: str = Field(primary_key=True)
    verifier: str
    nonce: str
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )


class LoginRow(SQLModel, table=True):
    __tablename__ = "auth_sessions"
    token_hash: str = Field(primary_key=True)
    athlete_id: UUID = Field(foreign_key="athletes.id", ondelete="CASCADE", index=True)
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )


class ExerciseRow(SQLModel, table=True):
    __tablename__ = "exercises"
    id: UUID = Field(primary_key=True)
    athlete_id: UUID = Field(foreign_key="athletes.id", ondelete="CASCADE", index=True)
    name: str
    category: str
    main: bool
    archived: bool


class PlanRow(SQLModel, table=True):
    __tablename__ = "plans"
    __table_args__ = (
        Index(
            "uq_active_plan",
            "athlete_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )
    id: UUID = Field(primary_key=True)
    athlete_id: UUID = Field(foreign_key="athletes.id", ondelete="CASCADE", index=True)
    status: str = Field(sa_column=Column(String(16), nullable=False))
    payload: dict[str, object] = Field(sa_column=Column(JSON, nullable=False))


class TemplateRow(SQLModel, table=True):
    __tablename__ = "plan_templates"
    token_hash: str = Field(primary_key=True)
    athlete_id: UUID = Field(foreign_key="athletes.id", ondelete="CASCADE", index=True)
    payload: dict[str, object] = Field(sa_column=Column(JSON, nullable=False))


class SessionRow(SQLModel, table=True):
    __tablename__ = "training_sessions"
    __table_args__ = (
        UniqueConstraint("athlete_id", "plan_id", "day_id", "week"),
        Index(
            "uq_running_session",
            "athlete_id",
            unique=True,
            postgresql_where=text("ended_at IS NULL"),
            sqlite_where=text("ended_at IS NULL"),
        ),
    )
    id: UUID = Field(primary_key=True)
    athlete_id: UUID = Field(foreign_key="athletes.id", ondelete="CASCADE", index=True)
    # Historical references deliberately survive plan/slot deletion.
    plan_id: UUID = Field(index=True)
    day_id: UUID
    week: int
    started_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    ended_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    payload: dict[str, object] = Field(sa_column=Column(JSON, nullable=False))


class WeighInRow(SQLModel, table=True):
    __tablename__ = "bodyweights"
    __table_args__ = (UniqueConstraint("athlete_id", "date"),)
    id: UUID = Field(primary_key=True)
    athlete_id: UUID = Field(foreign_key="athletes.id", ondelete="CASCADE", index=True)
    date: date
    weight_kg: Decimal = Field(sa_column=Column(Numeric(16, 8), nullable=False))
