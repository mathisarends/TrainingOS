"""Remove bodyweight history and target preferences at the owner's request."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    users = sa.table("users", sa.column("id", sa.Uuid()), sa.column("preferences", sa.JSON()))
    connection = op.get_bind()
    for user_id, preferences in connection.execute(sa.select(users.c.id, users.c.preferences)):
        updated = {key: value for key, value in preferences.items() if key != "target_weight_kg"}
        connection.execute(users.update().where(users.c.id == user_id).values(preferences=updated))
    op.drop_table("bodyweights")


def downgrade() -> None:
    # Downgrading restores the schema, not the intentionally deleted measurements.
    op.create_table(
        "bodyweights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(16, 8), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date"),
    )
    op.create_index("ix_bodyweights_user_id", "bodyweights", ["user_id"])
