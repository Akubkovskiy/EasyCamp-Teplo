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
        
        # Синхронизация
        stats = await sync_all_avito_items(item_house_mapping)
        
        logger.info(
            f"✅ Avito sync completed: "
            f"total={stats['total']}, new={stats['new']}, "
            f"updated={stats['updated']}, errors={stats['errors']}"
        )
        
        # Уведомление если есть новые брони
        if stats['new'] > 0:
            await notify_new_bookings(stats['new'])
            
    except Exception as e:
        logger.error(f"❌ Avito sync failed: {e}", exc_info=True)


async def notify_new_bookings(count: int):
    """Отправить уведомление о новых бронях"""
    try:
        bot = Bot(token=settings.telegram_bot_token)
        
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=(
                f"🔔 <b>Новых броней из Avito: {count}</b>\n\n"
                f"Используйте /bookings для просмотра\n"
                f"Или /sync для синхронизации с Google Sheets"
            ),
            parse_mode="HTML"
        )
        
        await bot.session.close()
        logger.info(f"Sent notification about {count} new bookings")
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
