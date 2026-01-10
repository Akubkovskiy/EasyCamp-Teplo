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


settings = Settings(
    telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
    telegram_chat_id=int(os.environ["TELEGRAM_CHAT_ID"]),
    google_sheets_spreadsheet_id=os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
    google_sheets_credentials_file=os.environ.get("GOOGLE_SHEETS_CREDENTIALS_FILE", "google-credentials.json"),
)
