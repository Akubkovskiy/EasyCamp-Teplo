import asyncio
import logging

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from aiogram import Dispatcher
from app.telegram.middlewares.panel_guard import PanelGuardMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.rate_limiter import limiter
from app.middleware.request_logger import RequestLoggerMiddleware

from app.api.health import router as health_router
from app.api.site_leads import router as site_leads_router
from app.avito.webhook import router as avito_router
from app.avito.oauth import router as avito_oauth_router

from app.telegram.bot import bot
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
    cleaner_admin,
    cleaner_expenses,
    cleaner_task_flow,
    guest,
    guest_booking,
    settings_content,
)
from app.telegram.handlers.booking_management import booking_routers


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
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestLoggerMiddleware)
# Custom Setup Middleware (redirects to /setup if needed)
# TEMPORARY DISABLED for debugging booking UI
# from app.web.middleware.setup_middleware import SetupMiddleware
# app.add_middleware(SetupMiddleware)

from app.web.deps import AuthRedirectException  # noqa: E402

@app.exception_handler(AuthRedirectException)
async def auth_redirect_handler(request: Request, exc: AuthRedirectException):
    return RedirectResponse(url="/admin-web/login")


from app.api.houses import router as houses_api_router  # noqa: E402

app.include_router(health_router)
app.include_router(site_leads_router)
app.include_router(avito_router)
app.include_router(avito_oauth_router)
app.include_router(houses_api_router)

from fastapi.staticfiles import StaticFiles  # noqa: E402
from app.web.routers import auth_web, admin_web, setup_web, settings_web, house_web, booking_web  # noqa: E402

app.mount("/admin-web/static", StaticFiles(directory="app/web/static"), name="static")
app.include_router(setup_web.router)
app.include_router(auth_web.router)
app.include_router(admin_web.router)
app.include_router(settings_web.router)
app.include_router(house_web.router)
app.include_router(booking_web.router)


# -------------------------------------------------
# Telegram (aiogram)
# -------------------------------------------------

# -------------------------------------------------
# Telegram (aiogram)
# -------------------------------------------------

# -------------------------------------------------
# Telegram Handlers Registration
# -------------------------------------------------
# (Imports are at the top of the file)

dp = Dispatcher()
# Global callback guard: prevents cross-panel/role callback leaks
# (e.g., old buttons from other menus)
dp.callback_query.middleware(PanelGuardMiddleware())

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
dp.include_router(cleaner_admin.router)
dp.include_router(cleaner_expenses.router)
dp.include_router(cleaner_task_flow.router)
# guest_booking ДОЛЖЕН идти раньше guest, иначе F.contact из login-flow
# в guest.py перехватит контакт от self-service потока.
dp.include_router(guest_booking.router)
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

    # Initial sync on bot start if enabled (non-blocking)
    if settings.sync_on_bot_start:
        logger.info("🔄 Scheduling initial sync on bot startup...")
        
        async def background_initial_sync():
            """Фоновая синхронизация при старте"""
            try:
                from app.services.sheets_service import sheets_service
                await sheets_service.sync_if_needed(force=True)
                logger.info("✅ Initial sync completed")
            except Exception as e:
                logger.error(f"❌ Initial sync failed: {e}", exc_info=True)
        
        # Запускаем в фоне, не блокируя старт сервера
        asyncio.create_task(background_initial_sync())

    # Refresh user cache
    from app.telegram.auth.admin import refresh_users_cache

    await refresh_users_cache()
    logger.info("👥 User cache refreshed")

    # Set bot menu commands
    from app.telegram.commands import setup_commands
    await setup_commands(bot)

    logger.info("Starting Telegram polling")

    asyncio.create_task(dp.start_polling(bot))


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("FastAPI shutdown")

    # Stop scheduler
    from app.services.scheduler_service import scheduler_service

    scheduler_service.shutdown()
    await bot.session.close()
