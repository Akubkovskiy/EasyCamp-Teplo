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

    await notify_new_avito_event(event, request)

    return {"status": "ok"}
