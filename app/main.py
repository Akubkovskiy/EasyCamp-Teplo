from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(
    title="EasyCamp Avito Sync",
    description="Backend service for EasyCamp (Avito + Telegram)",
    version="0.1.0",
)

# Подключаем роутеры
app.include_router(health_router)
