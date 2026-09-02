"""Google Drive backup/restore orchestration for the EasyCamp SQLite database."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from app.core.config import Settings, settings
from app.services.sqlite_recovery import (
    RestoreGateError,
    RestoreResult,
    SQLiteRecoveryError,
    apply_sqlite_restore,
    create_sqlite_snapshot,
    resolve_sqlite_database_path,
)

logger = logging.getLogger(__name__)

BACKUP_MIME_TYPE = "application/x-sqlite3"
BACKUP_NAME_PREFIX = "easycamp_backup_"


def _drive_service(scopes: list[str]):
    credentials = service_account.Credentials.from_service_account_file(
        settings.google_sheets_credentials_file,
        scopes=scopes,
    )
    return build("drive", "v3", credentials=credentials)


def _backup_database_to_drive_sync() -> dict[str, Any]:
    database_path = resolve_sqlite_database_path(settings.database_url)
    if not database_path.is_file():
        raise SQLiteRecoveryError(f"Database file not found: {database_path}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{BACKUP_NAME_PREFIX}{timestamp}.db"

    with tempfile.TemporaryDirectory(prefix="easycamp-backup-") as temp_dir:
        snapshot_path = Path(temp_dir) / backup_filename
        validation = create_sqlite_snapshot(database_path, snapshot_path)

        service = _drive_service(["https://www.googleapis.com/auth/drive.file"])
        metadata = {
            "name": backup_filename,
            "mimeType": BACKUP_MIME_TYPE,
            "appProperties": {
                "sha256": validation.sha256,
                "sizeBytes": str(validation.size_bytes),
                "schemaFormat": "easycamp-sqlite-v1",
                "alembicRevision": validation.alembic_revision or "unversioned",
            },
        }
        media = MediaFileUpload(
            str(snapshot_path),
            mimetype=BACKUP_MIME_TYPE,
            resumable=True,
        )
        uploaded = (
            service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id,name,createdTime,md5Checksum,appProperties,size",
            )
            .execute()
        )

    logger.info(
        "SQLite snapshot uploaded to Drive: name=%s id=%s sha256=%s",
        uploaded.get("name", backup_filename),
        uploaded.get("id"),
        validation.sha256,
    )
    return uploaded


async def backup_database_to_drive() -> dict[str, Any]:
    """Upload a consistent SQLite backup without copying the live file."""

    logger.info("Starting SQLite snapshot backup")
    try:
        return await asyncio.to_thread(_backup_database_to_drive_sync)
    except Exception:
        logger.exception("SQLite backup failed")
        raise


def assert_restore_gate(config: Settings) -> None:
    """Require an explicit maintenance-only process before touching the DB."""

    if not config.restore_from_drive_enabled:
        raise RestoreGateError("RESTORE_FROM_DRIVE_ENABLED=true is required")
    if not config.restore_maintenance_mode:
        raise RestoreGateError("RESTORE_MAINTENANCE_MODE=true is required")
    if not config.restore_drive_file_id.strip():
        raise RestoreGateError("RESTORE_DRIVE_FILE_ID must select an exact backup")

    active_writers = {
        "ENABLE_AUTO_SYNC": config.enable_auto_sync,
        "SYNC_ON_BOT_START": config.sync_on_bot_start,
        "SYNC_ON_USER_INTERACTION": config.sync_on_user_interaction,
        "ENABLE_YANDEX_TRAVEL_SYNC": config.enable_yandex_travel_sync,
        "ENABLE_YANDEX_TRAVEL_PRICE_SYNC": config.enable_yandex_travel_price_sync,
        "ENABLE_AVITO_PRICE_SYNC": config.enable_avito_price_sync,
        "ENABLE_AUTO_DISCOUNTS": config.enable_auto_discounts,
    }
    enabled = sorted(name for name, value in active_writers.items() if value)
    if enabled:
        raise RestoreGateError(
            "Restore maintenance boot requires writer flags to be false: " + ", ".join(enabled)
        )


def _selected_drive_backup(service, file_id: str) -> dict[str, Any]:
    backup = (
        service.files()
        .get(
            fileId=file_id,
            fields="id,name,mimeType,createdTime,md5Checksum,appProperties,size,trashed",
        )
        .execute()
    )
    if backup.get("trashed"):
        raise SQLiteRecoveryError("Selected Drive backup is in trash")
    if backup.get("mimeType") != BACKUP_MIME_TYPE:
        raise SQLiteRecoveryError("Selected Drive file is not an EasyCamp SQLite backup")
    if not str(backup.get("name", "")).startswith(BACKUP_NAME_PREFIX):
        raise SQLiteRecoveryError("Selected Drive file name is not an EasyCamp backup")
    return backup


def _download_drive_file(service, file_id: str, destination_path: Path) -> None:
    request = service.files().get_media(fileId=file_id)
    with destination_path.open("wb") as handle:
        downloader = MediaIoBaseDownload(handle, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def _restore_drive_backup_sync() -> RestoreResult:
    assert_restore_gate(settings)
    target_path = resolve_sqlite_database_path(settings.database_url)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    service = _drive_service(["https://www.googleapis.com/auth/drive.readonly"])
    selected = _selected_drive_backup(service, settings.restore_drive_file_id.strip())
    logger.warning(
        "Maintenance restore selected Drive backup: name=%s id=%s created=%s",
        selected.get("name"),
        selected.get("id"),
        selected.get("createdTime"),
    )

    with tempfile.TemporaryDirectory(
        prefix=".easycamp-drive-restore-",
        dir=target_path.parent,
    ) as temp_dir:
        candidate_path = Path(temp_dir) / "candidate.db"
        _download_drive_file(service, str(selected["id"]), candidate_path)

        app_properties = selected.get("appProperties") or {}
        if app_properties.get("sha256"):
            checksum_algorithm = "sha256"
            expected_checksum = str(app_properties["sha256"])
        elif selected.get("md5Checksum"):
            checksum_algorithm = "md5"
            expected_checksum = str(selected["md5Checksum"])
        else:
            raise SQLiteRecoveryError(
                "Drive backup has no sha256 appProperty or md5Checksum; restore refused"
            )

        result = apply_sqlite_restore(
            candidate_path,
            target_path,
            maintenance_mode=settings.restore_maintenance_mode,
            allow_overwrite=settings.restore_allow_overwrite,
            expected_checksum=expected_checksum,
            checksum_algorithm=checksum_algorithm,
        )

    logger.warning(
        "SQLite restore installed atomically: target=%s sha256=%s rollback=%s",
        result.target_path,
        result.installed_sha256,
        result.rollback_path,
    )
    return result


async def restore_drive_backup() -> RestoreResult:
    """Restore the explicitly selected Drive backup in a maintenance boot."""

    try:
        return await asyncio.to_thread(_restore_drive_backup_sync)
    except Exception:
        logger.exception("SQLite maintenance restore failed")
        raise
