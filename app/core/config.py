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


settings = Settings(
    telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
    telegram_chat_id=int(os.environ["TELEGRAM_CHAT_ID"]),
    google_sheets_spreadsheet_id=os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
    google_sheets_credentials_file=os.environ.get("GOOGLE_SHEETS_CREDENTIALS_FILE", "google-credentials.json"),
    avito_client_id=os.environ.get("AVITO_CLIENT_ID", ""),
    avito_client_secret=os.environ.get("AVITO_CLIENT_SECRET", ""),
    avito_item_ids=os.environ.get("AVITO_ITEM_IDS", ""),
    avito_redirect_uri=os.environ.get("AVITO_REDIRECT_URI", "http://localhost:8000/avito/callback"),
)
