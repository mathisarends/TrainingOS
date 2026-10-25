import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config

from backend.settings import AppSettings


def migration_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).with_name("alembic")))
    config.set_main_option("sqlalchemy.url", AppSettings().database_url.replace("%", "%%"))
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply TrainingOS database migrations")
    parser.add_argument("revision", nargs="?", default="head")
    args = parser.parse_args()
    command.upgrade(migration_config(), args.revision)
