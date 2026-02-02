import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Загрузка переменных из .env
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
    avito_user_id: int = 75878034
    avito_item_ids: str = ""
    avito_redirect_uri: str = "http://localhost:8000/avito/callback"

    # Scheduler settings
    enable_auto_sync: bool = True
    avito_sync_interval_minutes: int = 5
    sheets_sync_interval_minutes: int = 5

    # Sync behavior settings
    sync_on_bot_start: bool = True
    sync_on_user_interaction: bool = True
    sync_cache_ttl_seconds: int = 30

    # Avito calendar settings
    booking_window_days: int = 180

    # Cleaner settings
    cleaning_notification_time: str = "20:00"

    # Webhook security settings
    # Mode: "off" = no verification, "warn" = log warning but allow, "enforce" = reject invalid
    avito_webhook_mode: str = "warn"  # Default: warn (safe rollout)
    avito_webhook_secret: str = ""  # If empty, behaves as "off" mode

    # Rate limiting settings
    rate_limit_enabled: bool = True  # Killswitch for quick disable
    rate_limit_webhook: str = "30/minute"  # Default: 30 requests per minute per IP

    # Logging settings
    log_format: str = "console"  # Options: "console", "json"
    log_slow_request_threshold_ms: int = 500  # Log timing only if duration > threshold


# Resolve database URL with preference for Docker volume path
env_db_url = os.environ.get("DATABASE_URL")
if not env_db_url or "./easycamp.db" in env_db_url:
    if os.path.exists("/app/data/easycamp.db"):
        final_db_url = "sqlite+aiosqlite:////app/data/easycamp.db"
    else:
        final_db_url = "sqlite+aiosqlite:///./easycamp.db"
else:
    final_db_url = env_db_url

settings = Settings(
    telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
    telegram_chat_id=int(os.environ["TELEGRAM_CHAT_ID"]),
    database_url=final_db_url,
    google_sheets_spreadsheet_id=os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
    google_sheets_credentials_file=os.environ.get(
        "GOOGLE_SHEETS_CREDENTIALS_FILE", "google-credentials.json"
    ),
    avito_client_id=os.environ.get("AVITO_CLIENT_ID", ""),
    avito_client_secret=os.environ.get("AVITO_CLIENT_SECRET", ""),
    avito_item_ids=os.environ.get("AVITO_ITEM_IDS", ""),
    avito_redirect_uri=os.environ.get(
        "AVITO_REDIRECT_URI", "http://localhost:8000/avito/callback"
    ),
    enable_auto_sync=os.environ.get("ENABLE_AUTO_SYNC", "true").lower() == "true",
    avito_sync_interval_minutes=int(os.environ.get("AVITO_SYNC_INTERVAL_MINUTES", "5")),
    sheets_sync_interval_minutes=int(
        os.environ.get("SHEETS_SYNC_INTERVAL_MINUTES", "5")
    ),
    sync_on_bot_start=os.environ.get("SYNC_ON_BOT_START", "true").lower() == "true",
    sync_on_user_interaction=os.environ.get("SYNC_ON_USER_INTERACTION", "true").lower()
    == "true",
    sync_cache_ttl_seconds=int(os.environ.get("SYNC_CACHE_TTL_SECONDS", "30")),
    booking_window_days=int(os.environ.get("BOOKING_WINDOW_DAYS", "180")),
    cleaning_notification_time=os.environ.get("CLEANING_NOTIFICATION_TIME", "20:00"),
    avito_webhook_mode=os.environ.get("AVITO_WEBHOOK_MODE", "warn"),
    avito_webhook_secret=os.environ.get("AVITO_WEBHOOK_SECRET", ""),
    rate_limit_enabled=os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true",
    rate_limit_webhook=os.environ.get("RATE_LIMIT_WEBHOOK", "30/minute"),
    log_format=os.environ.get("LOG_FORMAT", "console"),
    log_slow_request_threshold_ms=int(
        os.environ.get("LOG_SLOW_REQUEST_THRESHOLD_MS", "500")
    ),
)
