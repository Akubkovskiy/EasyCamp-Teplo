import asyncio
import logging

from fastapi import FastAPI

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import settings
from app.core.logging import setup_logging

from app.api.health import router as health_router
from app.avito.webhook import router as avito_router
from app.telegram.handlers.admin_menu import router as admin_router


# -------------------------------------------------
# Logging
# -------------------------------------------------

setup_logging()
logger = logging.getLogger(__name__)

logger.info("Starting application")


# -------------------------------------------------
# FastAPI
# -------------------------------------------------

app = FastAPI(
    title="EasyCamp Avito Sync",
    description="Admin bot + Avito integration",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(avito_router)


# -------------------------------------------------
# Telegram (aiogram)
# -------------------------------------------------

bot = Bot(
    token=settings.telegram_bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()
dp.include_router(admin_router)


# -------------------------------------------------
# Lifecycle
# -------------------------------------------------

@app.on_event("startup")
async def on_startup():
    logger.info("FastAPI startup")
    logger.info("Starting Telegram polling")

    asyncio.create_task(dp.start_polling(bot))


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("FastAPI shutdown")
    await bot.session.close()
