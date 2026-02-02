"""
Периодическая задача для автоматического обновления статусов броней
"""
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Moscow timezone for business logic (check-in/check-out transitions)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")


async def update_booking_statuses_job():
    """
    Автоматическое обновление статусов броней:
    - CONFIRMED/PAID -> CHECKED_IN (если check_in <= сегодня < check_out)
    - CHECKED_IN -> COMPLETED (если check_out <= сегодня)
    
    Note: Uses Moscow timezone for date comparisons regardless of server timezone.
    """
    logger.info("🔄 Starting automatic booking status update...")
    
    try:
        from app.database import AsyncSessionLocal
        from app.models import Booking, BookingStatus
        from sqlalchemy import select
        
        # Use Moscow timezone for correct date comparison
        today = datetime.now(MOSCOW_TZ).date()
        logger.info(f"📅 Today (Moscow): {today}")
        
        updated_count = 0
        
        async with AsyncSessionLocal() as session:
            # Получаем все активные брони
            stmt = select(Booking).where(
                Booking.status.in_([
                    BookingStatus.CONFIRMED,
                    BookingStatus.PAID,
                    BookingStatus.CHECKING_IN,
                    BookingStatus.CHECKED_IN,
                    BookingStatus.NEW
                ])
            )
            result = await session.execute(stmt)
            bookings = result.scalars().all()
            
            for booking in bookings:
                old_status = booking.status
                new_status = None
                
                # Логика обновления статусов
                if booking.status in [BookingStatus.CONFIRMED, BookingStatus.PAID, BookingStatus.NEW]:
                    # Если сегодня день заезда (check_in == сегодня)
                    if booking.check_in == today and booking.check_out > today:
                        new_status = BookingStatus.CHECKING_IN
                    # Если гость уже должен был заселиться (check_in < сегодня < check_out)
                    elif booking.check_in < today < booking.check_out:
                        new_status = BookingStatus.CHECKED_IN
                        
                elif booking.status == BookingStatus.CHECKING_IN:
                    # Если прошла ночь после заезда (check_in < сегодня < check_out)
                    if booking.check_in < today < booking.check_out:
                        new_status = BookingStatus.CHECKED_IN
                        
                elif booking.status == BookingStatus.CHECKED_IN:
                    # Если гость должен был выселиться (check_out <= сегодня)
                    if booking.check_out <= today:
                        new_status = BookingStatus.COMPLETED
                
                # Применяем изменение
                if new_status and new_status != old_status:
                    booking.status = new_status
                    updated_count += 1
                    
                    logger.info(
                        f"📝 Booking #{booking.id} ({booking.guest_name}): "
                        f"{old_status.value} -> {new_status.value}"
                    )
            
            # Сохраняем изменения
            if updated_count > 0:
                await session.commit()
                logger.info(f"✅ Updated {updated_count} booking statuses")
                
                # Триггерим синхронизацию с Google Sheets
                logger.info("Triggering Sheets sync due to status changes...")
                from app.services.sheets_service import sheets_service
                await sheets_service.sync_if_needed(force=True)
            else:
                logger.info("No status updates needed")
                
    except Exception as e:
        logger.error(f"❌ Status update job failed: {e}", exc_info=True)
