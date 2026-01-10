"""
Периодическая задача синхронизации с Google Sheets
"""
import logging
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Booking
from app.services.sheets_service import sheets_service

logger = logging.getLogger(__name__)


async def sync_sheets_job():
    """Периодическая синхронизация с Google Sheets"""
    logger.info("📊 Starting scheduled Google Sheets sync...")
    
    try:
        async with AsyncSessionLocal() as session:
            # Получаем все брони
            result = await session.execute(
                select(Booking).order_by(Booking.check_in)
            )
            bookings = result.scalars().all()
            
            if not bookings:
                logger.info("No bookings to sync")
                return
            
            # Синхронизация
            await sheets_service.sync_bookings_to_sheet(bookings)
            
            logger.info(f"✅ Synced {len(bookings)} bookings to Google Sheets")
            
    except Exception as e:
        logger.error(f"❌ Sheets sync failed: {e}", exc_info=True)
