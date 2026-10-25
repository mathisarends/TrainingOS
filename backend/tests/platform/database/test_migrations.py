import pytest
from alembic import command

from backend.platform.database.migrations import migration_config

pytestmark = pytest.mark.integration


def test_migration_matches_metadata_and_supports_round_trip(database_url: str) -> None:
    config = migration_config()
    command.check(config)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    command.check(config)
