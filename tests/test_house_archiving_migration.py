import sqlite3
from contextlib import closing

from alembic.config import Config

from alembic import command
from app.core.config import settings

PREVIOUS_REVISION = "c8b1a6f4d2e9"
TARGET_REVISION = "f2a4c6e8b0d1"


def _config(path) -> Config:
    config = Config("alembic.ini")
    db_path = str(path).replace("\\", "/")
    config.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_path}")
    return config


def test_house_archiving_migration_upgrade_and_downgrade(tmp_path, monkeypatch):
    database = tmp_path / "archive-migration.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript(
            f"""
            CREATE TABLE houses (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );
            INSERT INTO houses (id, name) VALUES (1, 'House 1');
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            );
            INSERT INTO alembic_version (version_num) VALUES ('{PREVIOUS_REVISION}');
            """
        )
        connection.commit()

    db_path = str(database).replace("\\", "/")
    monkeypatch.setattr(settings, "database_url", f"sqlite+aiosqlite:///{db_path}")
    config = _config(database)
    command.upgrade(config, TARGET_REVISION)

    with closing(sqlite3.connect(database)) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info('houses')")}
        indexes = {row[1] for row in connection.execute("PRAGMA index_list('houses')")}
        assert "is_active" in columns
        assert "ix_houses_is_active" in indexes
        assert connection.execute(
            "SELECT is_active FROM houses WHERE id=1"
        ).fetchone() == (1,)

    command.downgrade(config, PREVIOUS_REVISION)
    with closing(sqlite3.connect(database)) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info('houses')")}
        assert "is_active" not in columns
