import logging
import asyncio
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import select, and_, or_

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus, BookingSource
from app.services.sheets_service import sheets_service

logger = logging.getLogger(__name__)


class BookingService:
    """Сервис бизнес-логики для бронирований"""
    
    async def check_availability(
        self, 
        house_id: int, 
        check_in: date, 
        check_out: date, 
        exclude_booking_id: Optional[int] = None
    ) -> bool:
        """
        Проверка доступности дат.
        Возвращает True если даты свободны.
        """
        try:
            async with AsyncSessionLocal() as session:
                query = select(Booking).where(
                    Booking.house_id == house_id,
                    Booking.status != BookingStatus.CANCELLED,  # Исключаем только отмененные
                    or_(
                        and_(Booking.check_in <= check_in, Booking.check_out > check_in),     # Начинается внутри
                        and_(Booking.check_in < check_out, Booking.check_out >= check_out),   # Заканчивается внутри
                        and_(Booking.check_in >= check_in, Booking.check_out <= check_out)    # Полностью внутри
                    )
                )
                
                if exclude_booking_id:
                    query = query.where(Booking.id != exclude_booking_id)
                
                result = await session.execute(query)
                conflicts = result.scalars().all()
                
                return len(conflicts) == 0
                
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return False

    async def create_booking(self, data: dict) -> Optional[Booking]:
        """
        Создание новой брони
        """
        try:
            async with AsyncSessionLocal() as session:
                booking = Booking(
                    house_id=data['house_id'],
                    # user_id not in model yet, removing
                    guest_name=data['guest_name'],
                    guest_phone=data.get('guest_phone'),
                    check_in=data['check_in'],
                    check_out=data['check_out'],
                    guests_count=data.get('guests_count', 1),
                    total_price=data.get('total_price', 0),
                    status=BookingStatus.CONFIRMED,
                    source=BookingSource.TELEGRAM,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                session.add(booking)
                await session.commit()
                await session.refresh(booking)
                
                # Фоновая синхронизация с GS
                asyncio.create_task(self.sync_all_to_sheets())
                
                return booking
                
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            return None

    async def sync_all_to_sheets(self):
        """Синхронизация всех броней с Google Sheets"""
        try:
            async with AsyncSessionLocal() as session:
                from sqlalchemy.orm import joinedload
                stmt = select(Booking).options(joinedload(Booking.house)).order_by(Booking.check_in)
                result = await session.execute(stmt)
                bookings = result.scalars().all()
                
                # Выполняем синхронный gspread запрос в отдельном потоке
                await asyncio.to_thread(sheets_service.sync_bookings_to_sheet, bookings)
                logger.info("Google Sheets sync completed successfully.")
        except Exception as e:
            logger.error(f"Background Sheets sync failed: {e}")

    async def get_booking(self, booking_id: int) -> Optional[Booking]:
        """Получить бронь по ID с информацией о доме"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy.orm import joinedload
            stmt = select(Booking).options(joinedload(Booking.house)).where(Booking.id == booking_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def cancel_booking(self, booking_id: int) -> bool:
        """Отмена брони"""
        try:
            async with AsyncSessionLocal() as session:
                booking = await session.get(Booking, booking_id)
                if not booking:
                    return False
                
                booking.status = BookingStatus.CANCELLED
                booking.updated_at = datetime.now()
                await session.commit()
                
                # Фоновая синхронизация
                asyncio.create_task(self.sync_all_to_sheets())
                    
                return True
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}")
            return False

    async def update_booking(self, booking_id: int, **kwargs) -> bool:
        """Обновление данных брони"""
        try:
            async with AsyncSessionLocal() as session:
                booking = await session.get(Booking, booking_id)
                if not booking:
                    return False
                
                for key, value in kwargs.items():
                    if hasattr(booking, key):
                        setattr(booking, key, value)
                
                booking.updated_at = datetime.now()
                await session.commit()
                
                # Фоновая синхронизация
                asyncio.create_task(self.sync_all_to_sheets())
                    
                return True
        except Exception as e:
            logger.error(f"Error updating booking: {e}")
            return False


booking_service = BookingService()
