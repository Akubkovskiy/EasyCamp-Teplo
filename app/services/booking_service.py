import logging
import asyncio
from datetime import datetime, date, timezone
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus, BookingSource, House
from app.schemas.booking import BookingCreate, BookingUpdate
from app.services.sheets_service import sheets_service

logger = logging.getLogger(__name__)


class BookingService:
    """Сервис бизнес-логики для бронирований"""

    @staticmethod
    async def check_availability(
        db: AsyncSession,
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
            query = select(Booking).where(
                Booking.house_id == house_id,
                Booking.status != BookingStatus.CANCELLED,
                and_(Booking.check_in < check_out, Booking.check_out > check_in),
            )

            if exclude_booking_id:
                query = query.where(Booking.id != exclude_booking_id)

            # Only fetch first conflict, no need to load all
            result = await db.execute(query.limit(1))
            conflict = result.scalars().first()

            return conflict is None

        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return False

    @staticmethod
    async def get_available_houses(
        db: AsyncSession, check_in: date, check_out: date
    ) -> List[House]:
        """
        Получить список доступных домов на указанные даты.
        """
        try:
            # Находим занятые дома
            busy_houses_query = select(Booking.house_id).where(
                Booking.status != BookingStatus.CANCELLED,
                and_(Booking.check_in < check_out, Booking.check_out > check_in),
            )

            # Выбираем дома, которых нет в списке занятых
            query = select(House).where(House.id.not_in(busy_houses_query))
            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting available houses: {e}")
            return []

    @classmethod
    async def create_booking(cls, db: AsyncSession, booking_in: BookingCreate | dict) -> Optional[Booking]:
        """
        Создание новой брони.
        """
        try:
            # Convert dict to schema if needed
            if isinstance(booking_in, dict):
                booking_in = BookingCreate(**booking_in)
            
            # Single contract point: check availability before creating
            is_available = await cls.check_availability(
                db,
                house_id=booking_in.house_id,
                check_in=booking_in.check_in,
                check_out=booking_in.check_out,
            )
            if not is_available:
                logger.warning(
                    f"Cannot create booking: dates {booking_in.check_in} - {booking_in.check_out} "
                    f"not available for house {booking_in.house_id}"
                )
                return None

            # Calculate defaults if not provided in schema (schema has defaults but logic might be specific)
            # If commission is 0, owner gets full advance
            if booking_in.commission == 0:
                booking_in.prepayment_owner = booking_in.advance_amount

            booking = Booking(
                house_id=booking_in.house_id,
                guest_name=booking_in.guest_name,
                guest_phone=booking_in.guest_phone,
                check_in=booking_in.check_in,
                check_out=booking_in.check_out,
                guests_count=booking_in.guests_count,
                total_price=booking_in.total_price,
                advance_amount=booking_in.advance_amount,
                commission=booking_in.commission,
                prepayment_owner=booking_in.prepayment_owner,
                status=booking_in.status,
                source=booking_in.source,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.add(booking)
            await db.commit()
            await db.refresh(booking)

            # Блокировка дат в Avito
            await cls._block_avito_dates(booking)

            # Фоновая синхронизация с GS (safe wrapper)
            asyncio.create_task(cls._safe_background_sheets_sync())

            return booking

        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            return None

    @staticmethod
    async def _block_avito_dates(booking: Booking):
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

    @classmethod
    async def sync_all_to_sheets(cls):
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

    @classmethod
    async def _safe_background_sheets_sync(cls):
        """
        Safe wrapper for background sheets sync.
        Catches and logs all errors to prevent task crashes.
        """
        try:
            await cls.sync_all_to_sheets()
        except Exception as e:
            logger.error(f"Background sheets sync failed: {e}", exc_info=True)

    @staticmethod
    async def get_booking(db: AsyncSession, booking_id: int) -> Optional[Booking]:
        """Получить бронь по ID с информацией о доме"""
        from sqlalchemy.orm import joinedload

        stmt = (
            select(Booking)
            .options(joinedload(Booking.house))
            .where(Booking.id == booking_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_bookings(db: AsyncSession) -> List[Booking]:
        """Получить все брони"""
        from sqlalchemy.orm import joinedload
        stmt = select(Booking).options(joinedload(Booking.house)).order_by(Booking.check_in.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def cancel_booking(cls, db: AsyncSession, booking_id: int) -> bool:
        """Отмена брони"""
        try:
            booking = await db.get(Booking, booking_id)
            if not booking:
                return False

            booking.status = BookingStatus.CANCELLED
            booking.updated_at = datetime.now(timezone.utc)
            await db.commit()

            # Разблокировка дат в Avito
            await cls._unblock_avito_dates(booking)

            # Фоновая синхронизация (safe wrapper)
            asyncio.create_task(cls._safe_background_sheets_sync())

            return True
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}")
            return False

    @classmethod
    async def delete_booking(cls, db: AsyncSession, booking_id: int) -> bool:
        """
        Полное удаление брони из базы данных.
        ВНИМАНИЕ: Это действие необратимо!
        """
        try:
            booking = await db.get(Booking, booking_id)
            if not booking:
                logger.warning(f"Booking {booking_id} not found for deletion")
                return False

            logger.info(
                f"Deleting booking #{booking_id}: {booking.guest_name} "
                f"({booking.check_in} - {booking.check_out})"
            )

            # Разблокируем даты в Avito перед удалением
            await cls._unblock_avito_dates(booking)

            # Удаляем из базы
            await db.delete(booking)
            await db.commit()

            logger.info(f"✅ Booking #{booking_id} deleted successfully")

            # Фоновая синхронизация с Google Sheets (safe wrapper)
            asyncio.create_task(cls._safe_background_sheets_sync())

            return True
        except Exception as e:
            logger.error(f"❌ Error deleting booking {booking_id}: {e}", exc_info=True)
            return False

    @classmethod
    async def update_booking(
        cls, db: AsyncSession, booking_id: int, update_data: BookingUpdate | dict
    ) -> bool:
        """
        Обновление существующего бронирования.
        """
        try:
            booking = await db.get(Booking, booking_id)
            if not booking:
                logger.warning(f"Booking {booking_id} not found for update")
                return False

            # Преобразуем словарь в схему, если нужно
            if isinstance(update_data, dict):
                # Фильтруем None значения и создаем dict для обновления
                update_dict = {k: v for k, v in update_data.items() if v is not None}
            else:
                update_dict = update_data.model_dump(exclude_unset=True)

            # Проверяем доступность новых дат, если они изменились
            check_in = update_dict.get("check_in") or (update_data.check_in if hasattr(update_data, "check_in") else None)
            check_out = update_dict.get("check_out") or (update_data.check_out if hasattr(update_data, "check_out") else None)
            house_id = update_dict.get("house_id") or (update_data.house_id if hasattr(update_data, "house_id") else None)

            if check_in or check_out or house_id:
                new_check_in = check_in or booking.check_in
                new_check_out = check_out or booking.check_out
                new_house_id = house_id or booking.house_id

                # Проверяем доступность только если даты или дом изменились
                if (
                    new_check_in != booking.check_in
                    or new_check_out != booking.check_out
                    or new_house_id != booking.house_id
                ):
                    is_available = await cls.check_availability(
                        db,
                        house_id=new_house_id,
                        check_in=new_check_in,
                        check_out=new_check_out,
                        exclude_booking_id=booking_id,
                    )
                    if not is_available:
                        logger.warning(
                            f"Cannot update booking {booking_id}: dates {new_check_in} - "
                            f"{new_check_out} not available for house {new_house_id}"
                        )
                        return False

            # Обновляем поля
            for field, value in update_dict.items():
                if hasattr(booking, field):
                    setattr(booking, field, value)

            booking.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(booking)

            logger.info(f"✅ Booking #{booking_id} updated successfully")

            # Фоновая синхронизация
            asyncio.create_task(cls._safe_background_sheets_sync())

            return True

        except Exception as e:
            logger.error(f"❌ Error updating booking {booking_id}: {e}", exc_info=True)
            await db.rollback()
            return False
    @staticmethod
    async def create_or_update_avito_booking(
        db: AsyncSession, booking_payload: "AvitoBookingPayload"
    ) -> Optional[Booking]:
        """
        Создать или обновить бронь из Avito webhook.
        """
        try:
            from app.models import Booking, BookingSource, BookingStatus
            from app.services.avito_sync_service import map_avito_status
            from app.utils.validators import format_phone
            from decimal import Decimal
            import asyncio

            avito_id = str(booking_payload.avito_booking_id)

            # Check existence
            stmt = select(Booking).where(
                Booking.external_id == avito_id, Booking.source == BookingSource.AVITO
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            # Helper for prepayment
            def get_prepayment(payload) -> Decimal:
                # Payload is Pydantic model
                val = (
                    payload.prepayment
                    or payload.prepayment_amount
                    or payload.advance
                    or payload.deposit
                    or (payload.safe_deposit.total_amount if payload.safe_deposit else 0)
                    or 0
                )
                return Decimal(str(val))

            if existing:
                # Update
                new_status = map_avito_status(booking_payload.status)
                if existing.status != new_status:
                    existing.status = new_status
                    existing.updated_at = datetime.now(timezone.utc)
                
                # Update other fields if needed ...
                existing.advance_amount = get_prepayment(booking_payload)
                
                await db.commit()
                await db.refresh(existing)
                
                # Sync to sheets
                asyncio.create_task(BookingService._safe_background_sheets_sync())
                
                return existing

            else:
                # Create
                # We need house_id. Since webhook might not contain internal house_id, we need mapping.
                # But typically Avito webhook contains item_id.
                
                # Mapping item_id -> house_id
                from app.core.config import settings
                item_house_mapping = {}
                for pair in settings.avito_item_ids.split(","):
                    if ":" in pair:
                        item_id, hid = pair.strip().split(":")
                        item_house_mapping[int(item_id)] = int(hid)

                house_id = item_house_mapping.get(booking_payload.item_id)
                if not house_id:
                    logger.error(f"Unknown Avito item_id {booking_payload.item_id}")
                    return None

                contact = booking_payload.contact or {}
                # Handle contact if it is object or dict (Pydantic)
                guest_name = getattr(contact, "name", "Гость Avito")
                guest_phone = getattr(contact, "phone", "")

                new_booking = Booking(
                    house_id=house_id,
                    guest_name=guest_name,
                    guest_phone=format_phone(guest_phone),
                    check_in=datetime.strptime(booking_payload.check_in, "%Y-%m-%d").date(),
                    check_out=datetime.strptime(booking_payload.check_out, "%Y-%m-%d").date(),
                    guests_count=booking_payload.guest_count or 1,
                    total_price=Decimal(str(booking_payload.base_price or 0)),
                    status=map_avito_status(booking_payload.status),
                    source=BookingSource.AVITO,
                    external_id=avito_id,
                    advance_amount=get_prepayment(booking_payload),
                    commission=Decimal(
                        str(booking_payload.safe_deposit.tax if booking_payload.safe_deposit else 0)
                    ),
                    prepayment_owner=Decimal(
                        str(booking_payload.safe_deposit.owner_amount if booking_payload.safe_deposit else 0)
                    ),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

                db.add(new_booking)
                await db.commit()
                await db.refresh(new_booking)
                
                # Sync to sheets
                asyncio.create_task(BookingService._safe_background_sheets_sync())

                return new_booking

        except Exception as e:
            logger.error(f"Error processing Avito booking {booking_payload.avito_booking_id}: {e}", exc_info=True)
            return None
