"""
Сервис синхронизации броней из Avito API
"""
from typing import List
from datetime import datetime
from decimal import Decimal
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus, BookingSource, House
from app.services.avito_api_service import avito_api_service
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


def map_avito_status(avito_status: str) -> BookingStatus:
    """Маппинг статусов Avito на статусы системы"""
    mapping = {
        "active": BookingStatus.CONFIRMED,
        "pending": BookingStatus.NEW,
        "cancelled": BookingStatus.CANCELLED
    }
    return mapping.get(avito_status, BookingStatus.NEW)


async def sync_avito_bookings(item_id: int, house_id: int) -> dict:
    """
    Синхронизация броней из Avito для одного объявления
    
    Args:
        item_id: ID объявления на Avito
        house_id: ID домика в нашей системе
        
    Returns:
        Статистика синхронизации
    """
    logger.info(f"Starting sync for Avito item {item_id} -> house {house_id}")
    
    stats = {
        "total": 0,
        "new": 0,
        "updated": 0,
        "errors": 0
    }
    
    try:
        # Получаем брони из Avito
        bookings_data = avito_api_service.get_bookings_for_period(item_id)
        stats["total"] = len(bookings_data)
        
        async with AsyncSessionLocal() as session:
            for booking_data in bookings_data:
                try:
                    await process_avito_booking(session, booking_data, house_id, stats)
                except Exception as e:
                    logger.error(f"Error processing booking {booking_data.get('avito_booking_id')}: {e}")
                    stats["errors"] += 1
            
            await session.commit()
        
        logger.info(f"Sync completed: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to sync Avito bookings: {e}")
        stats["errors"] += 1
        return stats


async def process_avito_booking(
    session: Session, 
    booking_data: dict, 
    house_id: int,
    stats: dict
):
    """Обработка одной брони из Avito"""
    avito_id = str(booking_data['avito_booking_id'])
    
    # Проверка существования
    stmt = select(Booking).where(
        Booking.external_id == avito_id,
        Booking.source == BookingSource.AVITO
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        # Обновить статус если изменился
        new_status = map_avito_status(booking_data['status'])
        if existing.status != new_status:
            existing.status = new_status
            existing.updated_at = datetime.now()
            stats["updated"] += 1
            logger.info(f"Updated booking {avito_id}: {existing.status} -> {new_status}")
    else:
        # Создать новую бронь
        contact = booking_data.get('contact', {})
        
        new_booking = Booking(
            house_id=house_id,
            guest_name=contact.get('name', 'Гость Avito'),
            guest_phone=contact.get('phone', ''),
            check_in=datetime.strptime(booking_data['check_in'], '%Y-%m-%d').date(),
            check_out=datetime.strptime(booking_data['check_out'], '%Y-%m-%d').date(),
            guests_count=booking_data.get('guest_count', 1),
            total_price=Decimal(str(booking_data.get('base_price', 0))),
            status=map_avito_status(booking_data['status']),
            source=BookingSource.AVITO,
            external_id=avito_id
        )
        
        session.add(new_booking)
        stats["new"] += 1
        logger.info(f"Created new booking {avito_id}")


async def sync_all_avito_items(item_house_mapping: dict) -> dict:
    """
    Синхронизация всех объявлений Avito
    
    Args:
        item_house_mapping: Словарь {item_id: house_id}
        
    Returns:
        Общая статистика
    """
    total_stats = {
        "total": 0,
        "new": 0,
        "updated": 0,
        "errors": 0
    }
    
    for item_id, house_id in item_house_mapping.items():
        stats = await sync_avito_bookings(item_id, house_id)
        
        total_stats["total"] += stats["total"]
        total_stats["new"] += stats["new"]
        total_stats["updated"] += stats["updated"]
        total_stats["errors"] += stats["errors"]
    
    return total_stats
