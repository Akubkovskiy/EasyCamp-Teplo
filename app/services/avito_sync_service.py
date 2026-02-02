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
from app.utils.validators import format_phone


logger = logging.getLogger(__name__)


def map_avito_status(avito_status: str) -> BookingStatus:
    """Маппинг статусов Avito на статусы системы"""
    mapping = {
        "active": BookingStatus.CONFIRMED,
        "pending": BookingStatus.NEW,
        "cancelled": BookingStatus.CANCELLED,
        "canceled": BookingStatus.CANCELLED
    }
    return mapping.get(avito_status, BookingStatus.NEW)


async def sync_avito_bookings(item_id: int, house_id: int) -> dict:
    """
    Синхронизация броней из Avito для одного объявления
    
    Args:
        item_id: ID объявления на Avito
        house_id: ID домика в нашей системе
        
    Returns:
        Словарь с ключами:
        - total (int)
        - new_bookings (List[Booking])
        - updated_bookings (List[Booking])
        - errors (int)
    """
    logger.info(f"Starting sync for Avito item {item_id} -> house {house_id}")
    
    stats = {
        "total": 0,
        "new_bookings": [],
        "updated_bookings": [],
        "errors": 0
    }
    
    try:
        # Получаем брони из Avito
        bookings_data = avito_api_service.get_bookings_for_period(item_id)
        stats["total"] = len(bookings_data)
        
        async with AsyncSessionLocal() as session:
            # 1. Обработка полученных броней
            seen_external_ids = set()
            for booking_data in bookings_data:
                try:
                    await process_avito_booking(session, booking_data, house_id, stats)
                    seen_external_ids.add(str(booking_data.get('avito_booking_id')))
                except Exception as e:
                    logger.error(f"Error processing booking {booking_data.get('avito_booking_id')}: {e}")
                    stats["errors"] += 1
            
            # 2. Сверка (Reconciliation) - поиск пропавших броней
            from datetime import timedelta
            from app.core.config import settings
            
            today = datetime.now().date()
            end_date = today + timedelta(days=settings.booking_window_days)
            
            # Ищем активные локальные брони Avito, которых нет в ответе API
            stmt = select(Booking).where(
                Booking.source == BookingSource.AVITO,
                Booking.house_id == house_id,
                Booking.check_in >= today,
                Booking.check_in <= end_date,
                Booking.status.in_([
                    BookingStatus.NEW, 
                    BookingStatus.CONFIRMED, 
                    BookingStatus.PAID, 
                    BookingStatus.CHECKING_IN
                ]),
                Booking.external_id.notin_(seen_external_ids)
            )
            
            result = await session.execute(stmt)
            stale_bookings = result.scalars().all()
            
            for stale in stale_bookings:
                if stale.status == BookingStatus.NEW:
                    # Удаляем "мусор" (неподтвержденные заявки, исчезнувшие с Avito)
                    logger.info(f"🗑 Deleting stale NEW booking {stale.id} (ext: {stale.external_id})")
                    await session.delete(stale)
                    # Можно добавить счетчик удаленных, если нужно
                else:
                    # Важные брони помечаем как отмененные
                    logger.info(f"❌ Cancelling stale booking {stale.id} (ext: {stale.external_id}, status: {stale.status})")
                    stale.status = BookingStatus.CANCELLED
                    stale.updated_at = datetime.now()
                    stats["updated_bookings"].append(stale) # Добавляем для уведомления
            
            await session.commit()
        
        logger.info(f"Sync completed: total={stats['total']}, new={len(stats['new_bookings'])}, updated={len(stats['updated_bookings'])}")
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
    # Robust logging for debugging
    import json
    try:
        logger.info(f"DEBUG_AVITO_PAYLOAD: {json.dumps(booking_data, default=str)}")
    except Exception:
        logger.info(f"DEBUG_AVITO_PAYLOAD: {booking_data}")

    avito_id = str(booking_data['avito_booking_id'])
    
    # Helper to extract prepayment/advance amount
    def get_prepayment(data: dict) -> Decimal:
        val = data.get('prepayment') \
              or data.get('prepayment_amount') \
              or data.get('advance') \
              or data.get('deposit') \
              or (data.get('safe_deposit') or {}).get('total_amount') \
              or 0
        return Decimal(str(val))

    # Проверка существования
    stmt = select(Booking).where(
        Booking.external_id == avito_id,
        Booking.source == BookingSource.AVITO
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        is_updated = False
        
        # Обновить статус если изменился
        new_status = map_avito_status(booking_data['status'])
        if existing.status != new_status:
            existing.status = new_status
            existing.updated_at = datetime.now()
            is_updated = True
            logger.info(f"Updated booking {avito_id}: {existing.status} -> {new_status}")
            
        # Update commission and owner prepayment
        safe_deposit = booking_data.get('safe_deposit') or {}
        new_commission = Decimal(str(safe_deposit.get('tax', 0)))
        new_owner_prep = Decimal(str(safe_deposit.get('owner_amount', 0)))
        
        if existing.commission != new_commission or existing.prepayment_owner != new_owner_prep:
            existing.commission = new_commission
            existing.prepayment_owner = new_owner_prep
            existing.updated_at = datetime.now()
            # Commission update doesn't necessarily warrant a user notification, but we track it
            
        # Update advance amount if changed
        new_advance = get_prepayment(booking_data)
        if existing.advance_amount != new_advance:
            existing.advance_amount = new_advance
            existing.updated_at = datetime.now()
            is_updated = True

        if is_updated:
            # Ensure house is loaded for notification
            house = await session.get(House, house_id)
            existing.house = house 
            stats["updated_bookings"].append(existing)

    else:
        # Создать новую бронь
        contact = booking_data.get('contact', {})
        
        # Extract name with safety checks
        raw_name = contact.get('name')
        guest_name = raw_name if raw_name else 'Гость Avito'
        
        new_booking = Booking(
            house_id=house_id,
            guest_name=guest_name,
            guest_phone=format_phone(contact.get('phone', '')),
            check_in=datetime.strptime(booking_data['check_in'], '%Y-%m-%d').date(),
            check_out=datetime.strptime(booking_data['check_out'], '%Y-%m-%d').date(),
            guests_count=booking_data.get('guest_count', 1),
            total_price=Decimal(str(booking_data.get('base_price', 0))),
            status=map_avito_status(booking_data['status']),
            source=BookingSource.AVITO,
            external_id=avito_id,
            advance_amount=get_prepayment(booking_data),
            commission=Decimal(str((booking_data.get('safe_deposit') or {}).get('tax', 0))),
            prepayment_owner=Decimal(str((booking_data.get('safe_deposit') or {}).get('owner_amount', 0)))
        )
        
        session.add(new_booking)
        
        # Need to commit or flush to get ID, and load house
        await session.flush()
        house = await session.get(House, house_id)
        new_booking.house = house
        
        stats["new_bookings"].append(new_booking)
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
        "new_bookings": [],
        "updated_bookings": [],
        "errors": 0
    }
    
    for item_id, house_id in item_house_mapping.items():
        stats = await sync_avito_bookings(item_id, house_id)
        
        total_stats["total"] += stats["total"]
        total_stats["new_bookings"].extend(stats["new_bookings"])
        total_stats["updated_bookings"].extend(stats["updated_bookings"])
        total_stats["errors"] += stats["errors"]
    
    return total_stats
