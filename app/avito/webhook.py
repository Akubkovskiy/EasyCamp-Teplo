import logging

from fastapi import APIRouter

from app.avito.schemas import AvitoWebhookEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/avito", tags=["avito"])


@router.post("/webhook")
async def avito_webhook(event: AvitoWebhookEvent):
    logger.info("Avito webhook received: %s", event)

    return {"status": "ok"}
