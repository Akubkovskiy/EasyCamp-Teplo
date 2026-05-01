"""
Периодическая задача синхронизации с Avito API
"""

import logging
from aiogram import Bot

from app.core.config import settings
from app.services.avito_sync_service import sync_all_avito_items
from app.services.notification_service import send_safe

logger = logging.getLogger(__name__)


async def sync_avito_job():
    """Периодическая синхронизация броней из Avito"""
    logger.info("🔄 Starting scheduled Avito sync...")

    try:
        # Парсим маппинг item_id:house_id
        item_house_mapping = {}
        for pair in settings.avito_item_ids.split(","):
            pair = pair.strip()
            if ":" in pair:
                item_id, house_id = pair.split(":")
                item_house_mapping[int(item_id)] = int(house_id)

        if not item_house_mapping:
            logger.warning("No item IDs configured for Avito sync")
            return

        # Синхронизация броней из Avito в БД
        stats = await sync_all_avito_items(item_house_mapping)

        logger.info(
            f"✅ Avito sync completed: "
            f"total={stats['total']}, new={len(stats['new_bookings'])}, "
            f"updated={len(stats['updated_bookings'])}, errors={stats['errors']}"
        )

        # Проверка и синхронизация локальных броней в Avito
        logger.info("🔍 Verifying local bookings in Avito...")
        await verify_local_bookings_in_avito(item_house_mapping)

        # Уведомления о новых бронях
        if stats["new_bookings"]:
            await notify_new_bookings(stats["new_bookings"])

        # Уведомления об обновленных бронях
        if stats["updated_bookings"]:
            await notify_updated_bookings(stats["updated_bookings"])

        # Если были изменения, запускаем синхронизацию с таблицей
        if stats["new_bookings"] or stats["updated_bookings"]:
            logger.info("Triggering Sheets sync due to Avito changes...")
            from app.services.sheets_service import sheets_service

            await sheets_service.sync_if_needed(force=True)

    except Exception as e:
        logger.error(f"❌ Avito sync failed: {e}", exc_info=True)


async def verify_local_bookings_in_avito(item_house_mapping: dict):
    """Проверить и синхронизировать локальные брони в Avito"""
    try:
        from app.database import AsyncSessionLocal
        from app.models import Booking, BookingStatus
        from sqlalchemy import select
        from datetime import datetime, timedelta
        from app.services.avito_api_service import avito_api_service
        import asyncio

        async with AsyncSessionLocal() as session:
            # Получаем все активные брони из БД
            today = datetime.now().date()
            end_date = today + timedelta(days=settings.booking_window_days)

            result = await session.execute(
                select(Booking).where(
                    Booking.status.in_(
                        [
                            BookingStatus.NEW,
                            BookingStatus.CONFIRMED,
                            BookingStatus.PAID,
                            BookingStatus.CHECKING_IN,
                            BookingStatus.CHECKED_IN,
                        ]
                    ),
                    Booking.check_in >= today,
                    Booking.check_out <= end_date,
                )
            )
            local_bookings = result.scalars().all()

            # ВАЖНО: для обновления интервалов доступности в Avito используем ТОЛЬКО
            # брони НЕ из Avito (ручные блоки). Avito сам управляет датами своих броней
            # внутри. Если мы отправим в /intervals Авито-бронь с pending-статусом,
            # Avito интерпретирует это как конфликт и может отменить заявку гостя.
            # Авито-брони со статусом NEW соответствуют pending на стороне Авито.
            from app.models import BookingSource
            manual_bookings = [
                b for b in local_bookings
                if b.source != BookingSource.AVITO
            ]

            logger.info(
                f"Found {len(local_bookings)} active local bookings to verify "
                f"({len(manual_bookings)} non-Avito for calendar sync)"
            )

            # Группируем брони по домам (только ручные — не Авито)
            bookings_by_house = {}
            for booking in manual_bookings:
                if booking.house_id not in bookings_by_house:
                    bookings_by_house[booking.house_id] = []
                bookings_by_house[booking.house_id].append(booking)

            # Проверяем каждый дом
            stats = {"updated": 0, "errors": 0}

            for item_id, house_id in item_house_mapping.items():
                house_bookings = bookings_by_house.get(house_id, [])

                logger.info(
                    f"Syncing calendar for house {house_id} (item {item_id}) using {len(house_bookings)} bookings"
                )

                # Вызываем обновление синхронно через asyncio.to_thread
                success = await asyncio.to_thread(
                    avito_api_service.update_calendar_from_local,
                    item_id,
                    house_bookings,
                )

                if success:
                    stats["updated"] += 1
                else:
                    stats["errors"] += 1

            logger.info(
                f"✅ Calendar sync complete: "
                f"updated={stats['updated']}, errors={stats['errors']}"
            )

    except Exception as e:
        logger.error(f"❌ Failed to verify local bookings: {e}", exc_info=True)


async def notify_new_bookings(bookings: list):
    """Отправить уведомление о новых бронях"""
    from app.services.cleaner_notify import notify_cleaners_new_booking

    bot = Bot(token=settings.telegram_bot_token)
    try:
        for booking in bookings:
            house_name = booking.house.name if booking.house else f"House {booking.house_id}"
            text = (
                f"🆕 <b>Новая бронь (Avito)</b>\n\n"
                f"🏠 <b>{house_name}</b>\n"
                f"👤 {booking.guest_name}\n"
                f"📞 {booking.guest_phone}\n"
                f"📅 {booking.check_in.strftime('%d.%m')} - {booking.check_out.strftime('%d.%m')}\n"
                f"💰 {booking.total_price}₽ (Предоплата: {booking.advance_amount}₽)"
            )
            await send_safe(bot, settings.telegram_chat_id, text, context=f"avito_new booking={booking.id}")
            await notify_cleaners_new_booking(bot, booking)

        logger.info(f"Sent notifications about {len(bookings)} new bookings")
    finally:
        await bot.session.close()


async def notify_updated_bookings(bookings: list):
    """Отправить уведомление об обновлении броней"""
    from app.models import BookingStatus
    from app.services.cleaner_notify import notify_cleaners_booking_cancelled

    _status_map = {
        "confirmed": "✅ Подтверждено",
        "cancelled": "❌ Отменено",
        "new": "⏳ Требуется подтверждение!",
        "paid": "💰 Оплачено",
    }

    bot = Bot(token=settings.telegram_bot_token)
    try:
        for booking in bookings:
            house_name = booking.house.name if booking.house else f"House {booking.house_id}"
            status_text = _status_map.get(booking.status.value, booking.status.value)
            text = (
                f"🔄 <b>Бронь обновлена (Avito)</b>\n\n"
                f"🏠 <b>{house_name}</b>\n"
                f"👤 {booking.guest_name}\n"
                f"📅 {booking.check_in.strftime('%d.%m')} - {booking.check_out.strftime('%d.%m')}\n"
                f"Статус: {status_text}\n"
                f"Предоплата: {booking.advance_amount}₽"
            )
            await send_safe(bot, settings.telegram_chat_id, text, context=f"avito_updated booking={booking.id}")

            if booking.status == BookingStatus.CANCELLED:
                await notify_cleaners_booking_cancelled(bot, booking)
    finally:
        await bot.session.close()
