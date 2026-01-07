from fastapi import FastAPI

from app.api.health import router as health_router
from app.avito.webhook import router as avito_router
from app.telegram.bot import init_bot

app = FastAPI(
    title="EasyCamp Avito Sync",
    description="Avito → Telegram notifier",
    version="0.1.0",
)


@app.on_event("startup")
async def startup_event():
    app.state.bot = init_bot()


@app.on_event("shutdown")
async def shutdown_event():
    bot = getattr(app.state, "bot", None)
    if bot:
        await bot.session.close()


app.include_router(health_router)
app.include_router(avito_router)
