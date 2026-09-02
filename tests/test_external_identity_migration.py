"""Safe-copy tests for the external booking identity migration."""

import sqlite3

import pytest
from alembic import command
from alembic.config import Config

from app.core.config import settings


PREVIOUS_REVISION = "a1b2c3d4e5f6"
INDEX_NAME = "uq_bookings_source_external_id"


def _legacy_database(path, *, with_duplicates: bool = False) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            f"""
            CREATE TABLE bookings (
                id INTEGER PRIMARY KEY,
                source VARCHAR(32) NOT NULL,
                external_id VARCHAR(255)
            );
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            );
            INSERT INTO alembic_version (version_num) VALUES ('{PREVIOUS_REVISION}');
            """
        )
        connection.execute(
            "INSERT INTO bookings (source, external_id) VALUES (?, ?)",
            ("YANDEX_TRAVEL", "yatr:legacy-1"),
        )
        if with_duplicates:
            connection.execute(
                "INSERT INTO bookings (source, external_id) VALUES (?, ?)",
                ("YANDEX_TRAVEL", "yatr:legacy-1"),
            )
        connection.commit()
    finally:
        connection.close()


def _index_names(path) -> set[str]:
    connection = sqlite3.connect(path)
    try:
        return {row[1] for row in connection.execute("PRAGMA index_list('bookings')")}
    finally:
        connection.close()


def _alembic_config(path) -> Config:
    config = Config("alembic.ini")
    db_path = str(path).replace("\\", "/")
    config.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_path}")
    return config


def test_external_identity_migration_upgrade_and_downgrade(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy-clean.db"
    _legacy_database(db_path)
    db_path_text = str(db_path).replace("\\", "/")
    db_url = f"sqlite+aiosqlite:///{db_path_text}"
    monkeypatch.setattr(settings, "database_url", db_url)
    config = _alembic_config(db_path)

    command.upgrade(config, "head")
    assert INDEX_NAME in _index_names(db_path)

    command.downgrade(config, PREVIOUS_REVISION)
    assert INDEX_NAME not in _index_names(db_path)


def test_external_identity_migration_refuses_legacy_duplicates(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy-duplicates.db"
    _legacy_database(db_path, with_duplicates=True)
    db_path_text = str(db_path).replace("\\", "/")
    db_url = f"sqlite+aiosqlite:///{db_path_text}"
    monkeypatch.setattr(settings, "database_url", db_url)

    with pytest.raises(RuntimeError, match="duplicate rows exist"):
        command.upgrade(_alembic_config(db_path), "head")

    assert INDEX_NAME not in _index_names(db_path)
