import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Загружаем переменные из .env
load_dotenv()


class Settings(BaseModel):
    telegram_bot_token: str
    telegram_chat_id: int
    database_url: str = "sqlite+aiosqlite:///./easycamp.db"
    
    # Google Sheets
    google_sheets_spreadsheet_id: str = ""
    google_sheets_credentials_file: str = "google-credentials.json"
    
    # Avito API
    avito_client_id: str = ""
    avito_client_secret: str = ""
    avito_user_id: int = 75878034  # Ваш user_id из документации
    avito_item_ids: str = ""  # Comma-separated list of item IDs
    avito_redirect_uri: str = "http://localhost:8000/avito/callback"  # Изменить на ngrok URL
    
    # Scheduler settings
    enable_auto_sync: bool = True
    avito_sync_interval_minutes: int = 5
    sheets_sync_interval_minutes: int = 5
    
    # Sync behavior settings
    sync_on_bot_start: bool = True
    sync_on_user_interaction: bool = True
    sync_cache_ttl_seconds: int = 30  # Minimum time between syncs
    
    # Avito calendar settings
    booking_window_days: int = 180  # На сколько дней вперед открыты брони


settings = Settings(
    telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
    telegram_chat_id=int(os.environ["TELEGRAM_CHAT_ID"]),
    google_sheets_spreadsheet_id=os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
    google_sheets_credentials_file=os.environ.get("GOOGLE_SHEETS_CREDENTIALS_FILE", "google-credentials.json"),
    avito_client_id=os.environ.get("AVITO_CLIENT_ID", ""),
    avito_client_secret=os.environ.get("AVITO_CLIENT_SECRET", ""),
    avito_item_ids=os.environ.get("AVITO_ITEM_IDS", ""),
    avito_redirect_uri=os.environ.get("AVITO_REDIRECT_URI", "http://localhost:8000/avito/callback"),
    enable_auto_sync=os.environ.get("ENABLE_AUTO_SYNC", "true").lower() == "true",
    avito_sync_interval_minutes=int(os.environ.get("AVITO_SYNC_INTERVAL_MINUTES", "5")),
    sheets_sync_interval_minutes=int(os.environ.get("SHEETS_SYNC_INTERVAL_MINUTES", "5")),
    sync_on_bot_start=os.environ.get("SYNC_ON_BOT_START", "true").lower() == "true",
    sync_on_user_interaction=os.environ.get("SYNC_ON_USER_INTERACTION", "true").lower() == "true",
    sync_cache_ttl_seconds=int(os.environ.get("SYNC_CACHE_TTL_SECONDS", "30")),
    booking_window_days=int(os.environ.get("BOOKING_WINDOW_DAYS", "180")),
)
