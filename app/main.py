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
from app.avito.oauth import router as avito_oauth_router
from app.telegram.handlers.admin_menu import router as admin_router
from app.telegram.handlers.availability import router as availability_router


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

# -------------------------------------------------
# Rate Limiting (slowapi)
# -------------------------------------------------
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Create limiter (used in endpoint decorators)
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.rate_limit_enabled,  # Killswitch via env
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(health_router)
app.include_router(avito_router)
app.include_router(avito_oauth_router)


# -------------------------------------------------
# Telegram (aiogram)
# -------------------------------------------------

# -------------------------------------------------
# Telegram (aiogram)
# -------------------------------------------------

from app.telegram.bot import bot

# Регистрация обработчиков
from app.telegram.handlers import (
    admin_menu,
    availability,
    bookings,
    contacts,
    sync,
    avito_fetch,
    scheduler,
    settings as settings_handler,
    houses,
    settings_users,
    cleaner,
    guest,
    settings_content,
)
from app.telegram.handlers.booking_management import booking_routers

dp = Dispatcher()
dp.include_router(admin_menu.router)
dp.include_router(availability.router)
dp.include_router(bookings.router)
dp.include_router(contacts.router)
dp.include_router(sync.router)
dp.include_router(avito_fetch.router)
dp.include_router(scheduler.router)
dp.include_router(settings_handler.router)
dp.include_router(settings_users.router)
dp.include_router(cleaner.router)
dp.include_router(guest.router)
dp.include_router(settings_content.router)
dp.include_router(houses.router)

for r in booking_routers:
    dp.include_router(r)


# -------------------------------------------------
# Lifecycle
# -------------------------------------------------


@app.on_event("startup")
async def on_startup():
    logger.info("FastAPI startup")

    # 0. Smart Recovery (Restore from Drive if DB missing)
    try:
        from app.services.backup_service import restore_latest_backup

        await restore_latest_backup()
    except Exception as e:
        logger.error(f"❌ Smart Recovery failed: {e}", exc_info=True)

    # Init DB
    from app.database import init_db

    await init_db()

    # Start scheduler
    from app.services.scheduler_service import scheduler_service

    scheduler_service.start()

    # Register auto-sync middleware if enabled
    if settings.sync_on_user_interaction:
        from app.telegram.middlewares import AutoSyncMiddleware

        dp.message.middleware(AutoSyncMiddleware())
        logger.info("✅ Auto-sync middleware registered")

    # Initial sync on bot start if enabled
    if settings.sync_on_bot_start:
        logger.info("🔄 Performing initial sync on bot startup...")
        try:
            from app.services.sheets_service import sheets_service

            await sheets_service.sync_if_needed(force=True)
            logger.info("✅ Initial sync completed")
        except Exception as e:
            logger.error(f"❌ Initial sync failed: {e}", exc_info=True)

    # Refresh user cache
    from app.telegram.auth.admin import refresh_users_cache

    await refresh_users_cache()
    logger.info("👥 User cache refreshed")

    logger.info("Starting Telegram polling")

    asyncio.create_task(dp.start_polling(bot))


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("FastAPI shutdown")

    # Stop scheduler
    from app.services.scheduler_service import scheduler_service

    scheduler_service.shutdown()
    await bot.session.close()
