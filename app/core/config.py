import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Загружаем переменные из .env
load_dotenv()


class Settings(BaseModel):
    telegram_bot_token: str
    telegram_chat_id: int


settings = Settings(
    telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
    telegram_chat_id=int(os.environ["TELEGRAM_CHAT_ID"]),
)
