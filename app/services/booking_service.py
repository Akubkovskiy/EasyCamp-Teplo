import logging
import asyncio
from datetime import datetime, date, timezone
from typing import List, Optional
from sqlalchemy import select, and_, or_

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus, BookingSource, House
from app.services.sheets_service import sheets_service

logger = logging.getLogger(__name__)


class BookingService:
    """Сервис бизнес-логики для бронирований"""

    async def check_availability(
        self,
        house_id: int,
        check_in: date,
        check_out: date,
        exclude_booking_id: Optional[int] = None,
    ) -> bool:
        """
        Проверка доступности дат.
        Возвращает True если даты свободны.
        """
        try:
            async with AsyncSessionLocal() as session:
                query = select(Booking).where(
                    Booking.house_id == house_id,
                    Booking.status != BookingStatus.CANCELLED,
                    and_(Booking.check_in < check_out, Booking.check_out > check_in),
                )

                if exclude_booking_id:
                    query = query.where(Booking.id != exclude_booking_id)

                # Only fetch first conflict, no need to load all
                result = await session.execute(query.limit(1))
                conflict = result.scalars().first()

                return conflict is None

        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return False

    async def get_available_houses(
        self, check_in: date, check_out: date
    ) -> List[House]:
        """
        Получить список доступных домов на указанные даты.
        """
        try:
            async with AsyncSessionLocal() as session:
                # Находим занятые дома
                busy_houses_query = select(Booking.house_id).where(
                    Booking.status != BookingStatus.CANCELLED,
                    and_(Booking.check_in < check_out, Booking.check_out > check_in),
                )

                # Выбираем дома, которых нет в списке занятых
                query = select(House).where(House.id.not_in(busy_houses_query))
                result = await session.execute(query)
                return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting available houses: {e}")
            return []

    async def create_booking(self, data: dict) -> Optional[Booking]:
        """
        Создание новой брони.

        Note: This method checks availability as a contract, but does NOT
        guarantee atomicity. For strict double-booking prevention, use
        database constraints (see tech debt: PR for locking/constraint).
        """
        try:
            # Single contract point: check availability before creating
            # (Does not prevent TOCTOU race, but ensures consistent logic)
            is_available = await self.check_availability(
                house_id=data["house_id"],
                check_in=data["check_in"],
                check_out=data["check_out"],
            )
            if not is_available:
                logger.warning(
                    f"Cannot create booking: dates {data['check_in']} - {data['check_out']} "
                    f"not available for house {data['house_id']}"
                )
                # TODO: Consider raising BookingNotAvailableError instead of returning None
                # when multiple handlers need to distinguish "unavailable" from "error"
                return None

            async with AsyncSessionLocal() as session:
                # User requested explicit fields for manual booking
                advance_amount = data.get("advance_amount", 0)
                commission = 0  # Telegram bookings have 0 commission

                # If commission is 0, owner gets full advance
                prepayment_owner = advance_amount

                # Parse status string to enum if needed
                status_raw = data.get("status", "new")
                try:
                    status_enum = BookingStatus(status_raw)
                except ValueError:
                    status_enum = BookingStatus.NEW

                booking = Booking(
                    house_id=data["house_id"],
                    guest_name=data["guest_name"],
                    guest_phone=data.get("guest_phone"),
                    check_in=data["check_in"],
                    check_out=data["check_out"],
                    guests_count=data.get("guests_count", 1),
                    total_price=data.get("total_price", 0),
                    advance_amount=advance_amount,
                    commission=commission,
                    prepayment_owner=prepayment_owner,
                    status=status_enum,
                    source=BookingSource.TELEGRAM,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

                session.add(booking)
                await session.commit()
                await session.refresh(booking)

                # Блокировка дат в Avito
                await self._block_avito_dates(booking)

                # Фоновая синхронизация с GS (safe wrapper)
                asyncio.create_task(self._safe_background_sheets_sync())

                return booking

        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            return None

    async def _block_avito_dates(self, booking: Booking):
        """Блокировка дат в Avito для брони"""
        try:
            # Получаем маппинг house_id -> avito_item_id
            from app.core.config import settings

            item_house_mapping = {}
            for pair in settings.avito_item_ids.split(","):
                if ":" in pair:
                    item_id, house_id = pair.strip().split(":")
                    item_house_mapping[int(house_id)] = int(item_id)

            # Проверяем, есть ли Avito объявление для этого дома
            avito_item_id = item_house_mapping.get(booking.house_id)

            if not avito_item_id:
                logger.info(
                    f"No Avito item ID for house {booking.house_id}, skipping calendar block"
                )
                return

            # Блокируем даты в Avito
            from app.services.avito_api_service import avito_api_service

            success = await asyncio.to_thread(
                avito_api_service.block_dates,
                avito_item_id,
                booking.check_in.isoformat(),
                booking.check_out.isoformat(),
                f"Бронь #{booking.id}: {booking.guest_name}",
            )

            if success:
                logger.info(f"✅ Avito dates blocked for booking #{booking.id}")
            else:
                logger.warning(
                    f"⚠️ Failed to block Avito dates for booking #{booking.id}"
                )

        except Exception as e:
            logger.error(f"Error blocking Avito dates: {e}", exc_info=True)
            # Не прерываем создание брони при ошибке Avito

    async def sync_all_to_sheets(self):
        """
        Синхронизация всех броней с Google Sheets.
        Raises exception on failure (caller should handle).
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy.orm import joinedload

            stmt = (
                select(Booking)
                .options(joinedload(Booking.house))
                .order_by(Booking.check_in)
            )
            result = await session.execute(stmt)
            bookings = result.scalars().all()

            # Выполняем синхронный gspread запрос в отдельном потоке
            await asyncio.to_thread(sheets_service.sync_bookings_to_sheet, bookings)
            logger.info("Google Sheets sync completed successfully.")

    async def _safe_background_sheets_sync(self):
        """
        Safe wrapper for background sheets sync.
        Catches and logs all errors to prevent task crashes.
        """
        try:
            await self.sync_all_to_sheets()
        except Exception as e:
            logger.error(f"Background sheets sync failed: {e}", exc_info=True)

    async def get_booking(self, booking_id: int) -> Optional[Booking]:
        """Получить бронь по ID с информацией о доме"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy.orm import joinedload

            stmt = (
                select(Booking)
                .options(joinedload(Booking.house))
                .where(Booking.id == booking_id)
            )
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
                booking.updated_at = datetime.now(timezone.utc)
                await session.commit()

                # Разблокировка дат в Avito
                await self._unblock_avito_dates(booking)

                # Фоновая синхронизация (safe wrapper)
                asyncio.create_task(self._safe_background_sheets_sync())

                return True
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}")
            return False

    async def delete_booking(self, booking_id: int) -> bool:
        """
        Полное удаление брони из базы данных.
        ВНИМАНИЕ: Это действие необратимо!
        """
        try:
            async with AsyncSessionLocal() as session:
                booking = await session.get(Booking, booking_id)
                if not booking:
                    logger.warning(f"Booking {booking_id} not found for deletion")
                    return False

                logger.info(
                    f"Deleting booking #{booking_id}: {booking.guest_name} "
                    f"({booking.check_in} - {booking.check_out})"
                )

                # Разблокируем даты в Avito перед удалением
                await self._unblock_avito_dates(booking)

                # Удаляем из базы
                await session.delete(booking)
                await session.commit()

                logger.info(f"✅ Booking #{booking_id} deleted successfully")

                # Фоновая синхронизация с Google Sheets (safe wrapper)
                asyncio.create_task(self._safe_background_sheets_sync())

                return True

        except Exception as e:
            logger.error(f"❌ Error deleting booking {booking_id}: {e}", exc_info=True)
            return False

    async def _unblock_avito_dates(self, booking: Booking):
        """Разблокировка дат в Avito при отмене брони"""
        try:
            # Получаем маппинг house_id -> avito_item_id
            from app.core.config import settings

            item_house_mapping = {}
            for pair in settings.avito_item_ids.split(","):
                if ":" in pair:
                    item_id, house_id = pair.strip().split(":")
                    item_house_mapping[int(house_id)] = int(item_id)

            # Проверяем, есть ли Avito объявление для этого дома
            avito_item_id = item_house_mapping.get(booking.house_id)

            if not avito_item_id:
                logger.info(
                    f"No Avito item ID for house {booking.house_id}, skipping calendar unblock"
                )
                return

            # Разблокируем даты в Avito
            from app.services.avito_api_service import avito_api_service

            success = await asyncio.to_thread(
                avito_api_service.unblock_dates,
                avito_item_id,
                booking.check_in.isoformat(),
                booking.check_out.isoformat(),
            )

            if success:
                logger.info(f"✅ Avito dates unblocked for booking #{booking.id}")
            else:
                logger.warning(
                    f"⚠️ Could not unblock Avito dates for booking #{booking.id}"
                )

        except Exception as e:
            logger.error(f"Error unblocking Avito dates: {e}", exc_info=True)
            # Не прерываем отмену брони при ошибке Avito

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

                booking.updated_at = datetime.now(timezone.utc)
                await session.commit()

                # Фоновая синхронизация (safe wrapper)
                asyncio.create_task(self._safe_background_sheets_sync())

                return True
        except Exception as e:
            logger.error(f"Error updating booking: {e}")
            return False


booking_service = BookingService()
