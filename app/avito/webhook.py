from fastapi import APIRouter, Request

from app.avito.schemas import AvitoWebhookEvent
from app.telegram.notifier import notify_new_avito_event

router = APIRouter(prefix="/avito", tags=["avito"])


@router.post("/webhook")
async def avito_webhook(
    event: AvitoWebhookEvent,
    request: Request,
):
    await notify_new_avito_event(event, request)
    return {"status": "ok"}
