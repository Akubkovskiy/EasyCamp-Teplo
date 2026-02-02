"""
Периодическая задача синхронизации с Avito API
"""
import logging
from aiogram import Bot

from app.core.config import settings
from app.services.avito_sync_service import sync_all_avito_items

logger = logging.getLogger(__name__)


async def sync_avito_job():
    """Периодическая синхронизация броней из Avito"""
    logger.info("🔄 Starting scheduled Avito sync...")
    
    try:
        # Парсим маппинг item_id:house_id
        item_house_mapping = {}
        for pair in settings.avito_item_ids.split(','):
            pair = pair.strip()
            if ':' in pair:
                item_id, house_id = pair.split(':')
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
        if stats['new_bookings']:
            await notify_new_bookings(stats['new_bookings'])
            
        # Уведомления об обновленных бронях
        if stats['updated_bookings']:
            await notify_updated_bookings(stats['updated_bookings'])
            
        # Если были изменения, запускаем синхронизацию с таблицей
        if stats['new_bookings'] or stats['updated_bookings']:
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
                    Booking.status.in_([
                        BookingStatus.NEW, 
                        BookingStatus.CONFIRMED, 
                        BookingStatus.PAID,
                        BookingStatus.CHECKING_IN,
                        BookingStatus.CHECKED_IN
                    ]),
                    Booking.check_in >= today,
                    Booking.check_out <= end_date
                )
            )
            local_bookings = result.scalars().all()
            
            logger.info(f"Found {len(local_bookings)} active local bookings to verify")
            
            # Группируем брони по домам
            bookings_by_house = {}
            for booking in local_bookings:
                if booking.house_id not in bookings_by_house:
                    bookings_by_house[booking.house_id] = []
                bookings_by_house[booking.house_id].append(booking)
            
            # Проверяем каждый дом
            stats = {'updated': 0, 'errors': 0}
            
            for item_id, house_id in item_house_mapping.items():
                house_bookings = bookings_by_house.get(house_id, [])
                
                logger.info(f"Syncing calendar for house {house_id} (item {item_id}) using {len(house_bookings)} bookings")
                
                # Вызываем обновление синхронно через asyncio.to_thread
                success = await asyncio.to_thread(
                    avito_api_service.update_calendar_from_local,
                    item_id,
                    house_bookings
                )
                
                if success:
                    stats['updated'] += 1
                else:
                    stats['errors'] += 1
            
            logger.info(
                f"✅ Calendar sync complete: "
                f"updated={stats['updated']}, errors={stats['errors']}"
            )
            
    except Exception as e:
        logger.error(f"❌ Failed to verify local bookings: {e}", exc_info=True)


async def notify_new_bookings(bookings: list):
    """Отправить уведомление о новых бронях"""
    try:
        bot = Bot(token=settings.telegram_bot_token)
        
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
            
            try:
                await bot.send_message(
                    chat_id=settings.telegram_chat_id,
                    text=text,
                    parse_mode="HTML"
                )
            except Exception as msg_err:
                logger.error(f"Failed to send individual booking notification: {msg_err}")
        
        await bot.session.close()
        logger.info(f"Sent notifications about {len(bookings)} new bookings")
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

async def notify_updated_bookings(bookings: list):
    """Отправить уведомление об обновлении броней"""
    try:
        bot = Bot(token=settings.telegram_bot_token)
        
        for booking in bookings:
            house_name = booking.house.name if booking.house else f"House {booking.house_id}"
            status_map = {
                'confirmed': '✅ Подтверждено',
                'cancelled': '❌ Отменено',
                'new': '⏳ Требуется подтверждение!',
                'paid': '💰 Оплачено'
            }
            status_text = status_map.get(booking.status.value, booking.status.value)
            
            text = (
                f"🔄 <b>Бронь обновлена (Avito)</b>\n\n"
                f"🏠 <b>{house_name}</b>\n"
                f"👤 {booking.guest_name}\n"
                f"📅 {booking.check_in.strftime('%d.%m')} - {booking.check_out.strftime('%d.%m')}\n"
                f"Статус: {status_text}\n"
                f"Предоплата: {booking.advance_amount}₽"
            )
            
            try:
                await bot.send_message(
                    chat_id=settings.telegram_chat_id,
                    text=text,
                    parse_mode="HTML"
                )
            except Exception as msg_err:
                logger.error(f"Failed to send individual booking notification: {msg_err}")
                
        await bot.session.close()

    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
