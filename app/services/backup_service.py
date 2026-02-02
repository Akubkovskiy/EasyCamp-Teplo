import os
import shutil
import logging
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.core.config import settings

logger = logging.getLogger(__name__)


async def backup_database_to_drive():
    """
    Creates a backup of the SQLite database and uploads it to Google Drive.
    """
    logger.info("📦 Starting database backup...")

    # Define paths
    # Assuming the database URL is like sqlite+aiosqlite:///path/to/db or just a file path
    # We need to parse the actual file path from config
    db_path = "easycamp.db"  # Default local

    # Try to parse from DATABASE_URL if strictly defined
    if "sqlite" in settings.database_url:
        parts = settings.database_url.split("///")
        if len(parts) > 1:
            db_path = parts[1]

    # For Docker, db_path might be absolute /data/easycamp.db.
    # But usually we just backup the file we know.
    # Let's verify existence.
    if not os.path.exists(db_path):
        # Fallback for Docker path if running inside container
        if os.path.exists("/app/data/easycamp.db"):
            db_path = "/app/data/easycamp.db"
        elif os.path.exists("data/easycamp.db"):
            db_path = "data/easycamp.db"

    if not os.path.exists(db_path):
        logger.error(f"❌ Database file not found at {db_path}. Backup failed.")
        return

    backup_filename = f"easycamp_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

    try:
        # 1. Authenticate
        scope = ["https://www.googleapis.com/auth/drive.file"]
        creds = service_account.Credentials.from_service_account_file(
            settings.google_sheets_credentials_file, scopes=scope
        )
        service = build("drive", "v3", credentials=creds)

        # 2. Upload
        logger.info(f"Uploading {db_path} as {backup_filename}...")

        file_metadata = {
            "name": backup_filename,
            "mimeType": "application/x-sqlite3",
            # 'parents': ['FOLDER_ID'] # Optional: if user wants a specific folder
        }

        media = MediaFileUpload(
            db_path, mimetype="application/x-sqlite3", resumable=True
        )

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        logger.info(f"✅ Backup successful! File ID: {file.get('id')}")

    except Exception as e:
        logger.error(f"❌ Backup failed: {e}", exc_info=True)


async def restore_latest_backup():
    """
    Checks Google Drive for the latest backup and restores it
    ONLY if the local database is missing or empty (size 0).
    """
    db_path = "easycamp.db"
    if "sqlite" in settings.database_url:
        parts = settings.database_url.split("///")
        if len(parts) > 1:
            db_path = parts[1]

    # Normalize path if inside Docker
    if os.path.exists("/app/data"):
        db_path = "/app/data/easycamp.db"
    elif os.path.exists("data"):
        # Ensure local data folder
        db_path = "data/easycamp.db"

    # Check eligibility
    if os.path.exists(db_path) and os.path.getsize(db_path) > 1024:
        logger.info(
            f"Database exists and is not empty ({os.path.getsize(db_path)} bytes). Skipping restore."
        )
        return

    logger.info("📦 Database missing or empty. Searching for backup on Drive...")

    try:
        # Authenticate
        scope = ["https://www.googleapis.com/auth/drive.readonly"]
        creds = service_account.Credentials.from_service_account_file(
            settings.google_sheets_credentials_file, scopes=scope
        )
        service = build("drive", "v3", credentials=creds)

        # Search
        query = "name contains 'easycamp_backup_' and mimeType = 'application/x-sqlite3' and trashed = false"
        results = (
            service.files()
            .list(
                q=query,
                orderBy="createdTime desc",
                pageSize=1,
                fields="files(id, name, createdTime)",
            )
            .execute()
        )
        files = results.get("files", [])

        if not files:
            logger.warning("⚠️ No backups found on Google Drive.")
            return

        latest = files[0]
        logger.info(
            f"🔄 Restoring latest backup: {latest['name']} (ID: {latest['id']})..."
        )

        # Download
        request = service.files().get_media(fileId=latest["id"])

        # Ensure dir exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        import io
        from googleapiclient.http import MediaIoBaseDownload

        with io.FileIO(db_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                # logger.info(f"Download {int(status.progress() * 100)}%.")

        logger.info("✅ Database restored successfully!")

    except Exception as e:
        logger.error(f"❌ Restore failed: {e}", exc_info=True)
