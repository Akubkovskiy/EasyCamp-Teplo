from app.avito.schemas import AvitoWebhookEvent
from app.core.config import settings
from fastapi import Request


async def notify_new_avito_event(
    event: AvitoWebhookEvent,
    request: Request,
) -> None:
    bot = request.app.state.bot

    text = (
        "<b>📩 Новое событие с Avito</b>\n\n"
        f"<b>Тип:</b> {event.event_type}\n"
        f"<b>Время:</b> {event.event_time}\n\n"
        f"<pre>{event.payload}</pre>"
    )

    await bot.send_message(
        chat_id=settings.telegram_chat_id,
        text=text,
    )
