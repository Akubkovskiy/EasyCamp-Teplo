"""
Периодическая задача синхронизации с Яндекс Путешествиями.

Запускается каждые YANDEX_TRAVEL_SYNC_INTERVAL_MINUTES минут (по умолчанию 15).
Polling вместо webhooks — API Яндекс Путешествий не поддерживает push.
"""

import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


async def sync_yandex_travel_job() -> None:
    """Основная задача синхронизации. Регистрируется в scheduler при старте."""

    if not settings.yandex_travel_oauth_token:
        logger.debug("YaTr: YANDEX_TRAVEL_OAUTH_TOKEN не задан — синхронизация пропущена")
        return

    if not settings.enable_yandex_travel_sync:
        logger.debug("YaTr: синхронизация отключена (ENABLE_YANDEX_TRAVEL_SYNC=false)")
        return

    logger.info("🔄 YaTr: запуск синхронизации...")

    try:
        from app.database import AsyncSessionLocal
        from app.services.yandex_travel_sync_service import sync_yatr_orders

        async with AsyncSessionLocal() as db:
            stats = await sync_yatr_orders(db)

        logger.info(
            "✅ YaTr sync: total=%d new=%d updated=%d errors=%d",
            stats["total"],
            len(stats["new_bookings"]),
            len(stats["updated_bookings"]),
            len(stats["errors"]),
        )

        # Уведомления о новых бронях
        if stats["new_bookings"]:
            await _notify_new_bookings(stats["new_bookings"])

        # Если были изменения — обновляем Google Sheets
        if stats["new_bookings"] or stats["updated_bookings"]:
            try:
                from app.services.sheets_service import sheets_service
                await sheets_service.sync_if_needed(force=True)
            except Exception as e:
                logger.warning("YaTr: не удалось обновить Sheets: %s", e)

        # Синхронизация локальных броней → Яндекс (блокировка дат)
        if settings.yandex_travel_room_ids:
            await _sync_local_bookings_to_yatr()

    except Exception as e:
        logger.error("❌ YaTr sync failed: %s", e, exc_info=True)


async def _notify_new_bookings(bookings) -> None:
    """Telegram-уведомление о новых бронях от Яндекс Путешествий."""
    try:
        from app.core.config import settings as s
        from app.services.notification_service import send_safe
        from aiogram import Bot

        bot = Bot(token=s.telegram_bot_token)
        for booking in bookings:
            nights = (booking.check_out - booking.check_in).days
            text = (
                f"🟡 <b>Новая бронь — Яндекс Путешествия</b>\n\n"
                f"🏠 {booking.house.name if booking.house else f'Домик #{booking.house_id}'}\n"
                f"📅 {booking.check_in.strftime('%d.%m.%Y')} — {booking.check_out.strftime('%d.%m.%Y')} ({nights} сут.)\n"
                f"👤 {booking.guest_name}\n"
                f"📞 {booking.guest_phone}\n"
                f"💰 {booking.total_price:,.0f} ₽\n"
                f"🆔 #{booking.id} | ext: {booking.external_id}"
            )
            await send_safe(bot, s.telegram_chat_id, text, parse_mode="HTML")
        await bot.session.close()
    except Exception as e:
        logger.error("YaTr: ошибка отправки уведомления: %s", e)


async def _sync_local_bookings_to_yatr() -> None:
    """
    Закрыть занятые даты в Яндекс Путешествиях на основе локальных броней.
    Вызывается после каждого sync-цикла.
    """
    from app.database import AsyncSessionLocal
    from app.models import Booking, BookingSource, BookingStatus
    from app.services.yandex_travel_api_service import yandex_travel_api_service
    from app.services.yandex_travel_sync_service import parse_hotel_room_mapping
    from sqlalchemy import select
    from datetime import date, timedelta

    hotel_room_mapping = parse_hotel_room_mapping()
    if not hotel_room_mapping:
        return

    # Инверсная карта: house_id → [(hotel_id, room_id)]
    house_to_rooms: dict = {}
    for key, house_id in hotel_room_mapping.items():
        hotel_id, _, room_id = key.partition("/")
        house_to_rooms.setdefault(house_id, []).append((hotel_id, room_id))

    today = date.today()
    window_end = today + timedelta(days=settings.booking_window_days)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Booking).where(
                Booking.status.in_([
                    BookingStatus.NEW,
                    BookingStatus.CONFIRMED,
                    BookingStatus.PAID,
                    BookingStatus.CHECKING_IN,
                ]),
                Booking.check_out >= today,
                Booking.check_in <= window_end,
                Booking.source != BookingSource.YANDEX_TRAVEL,
            )
        )
        local_bookings = result.scalars().all()

    for house_id, rooms in house_to_rooms.items():
        house_bookings = [b for b in local_bookings if b.house_id == house_id]
        for hotel_id, room_id in rooms:
            try:
                yandex_travel_api_service.close_dates_from_local_bookings(
                    hotel_id=hotel_id,
                    room_id=room_id,
                    local_bookings=house_bookings,
                )
            except Exception as e:
                logger.error("YaTr: ошибка блокировки дат %s/%s: %s", hotel_id, room_id, e)
