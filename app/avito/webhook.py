import logging
from fastapi import APIRouter, Request

from app.avito.schemas import AvitoWebhookEvent
from app.telegram.notifier import notify_new_avito_event


router = APIRouter(prefix="/avito", tags=["avito"])
logger = logging.getLogger(__name__)


@router.post("/webhook")
async def avito_webhook(
    event: AvitoWebhookEvent,
    request: Request,
):
    logger.info("Received Avito webhook: %s", event.event_type)
    
    # Пытаемся распарсить payload как бронь
    # В реальности нужно проверять event_type
    try:
        from app.database import AsyncSessionLocal
        from app.services.booking_service import create_or_update_avito_booking
        from app.avito.schemas import AvitoBookingPayload
        
        # Заглушка: если payload не соответствует, мы это увидим в логах
        # В продакшене нужно аккуратнее обрабатывать ошибки валидации
        booking_payload = AvitoBookingPayload(**event.payload)
        
        async with AsyncSessionLocal() as session:
            booking = await create_or_update_avito_booking(session, booking_payload)
            
        # Уведомляем с данными из БД
        await notify_new_avito_event(event, request, booking)
        
    except Exception as e:
        logger.error("Error processing Avito webhook: %s", e, exc_info=True)
        # Не падаем, чтобы Avito не слал повторы бесконечно (или падаем, если хотим retry)
        # Для MVP лучше вернуть 200 и залогировать ошибку

    return {"status": "ok"}
