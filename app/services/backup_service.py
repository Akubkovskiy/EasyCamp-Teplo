
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
    db_path = "easycamp.db" # Default local
    
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
        scope = ['https://www.googleapis.com/auth/drive.file']
        creds = service_account.Credentials.from_service_account_file(
            settings.google_sheets_credentials_file, scopes=scope
        )
        service = build('drive', 'v3', credentials=creds)

        # 2. Upload
        logger.info(f"Uploading {db_path} as {backup_filename}...")
        
        file_metadata = {
            'name': backup_filename,
            'mimeType': 'application/x-sqlite3'
            # 'parents': ['FOLDER_ID'] # Optional: if user wants a specific folder
        }
        
        media = MediaFileUpload(db_path, mimetype='application/x-sqlite3', resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        logger.info(f"✅ Backup successful! File ID: {file.get('id')}")
        
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}", exc_info=True)
