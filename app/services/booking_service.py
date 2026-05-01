import logging
import asyncio
from datetime import datetime, date, timezone
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    Booking,
    BookingStatus,
    CleaningPaymentEntryType,
    CleaningPaymentLedger,
    CleaningTask,
    CleaningTaskStatus,
    House,
    PaymentStatus,
    User,
)
from app.schemas.booking import BookingCreate, BookingUpdate
from app.avito.schemas import AvitoBookingPayload
from app.services.sheets_service import sheets_service

logger = logging.getLogger(__name__)


def extract_avito_contact_value(payload: AvitoBookingPayload, field: str) -> str | None:
    """
    Read guest contact fields from either nested contact data or legacy top-level payload fields.

    Avito payloads in this project exist in multiple shapes:
    - webhook payloads with contact.name / contact.phone
    - legacy/top-level guest_name / guest_phone fields
    The old code used getattr(contact, "...") on a dict, which silently forced
    the fallback guest name for valid webhook payloads.
    """
    contact = getattr(payload, "contact", None) or {}

    value = None
    if isinstance(contact, dict):
        value = contact.get(field)
    else:
        value = getattr(contact, field, None)

    if isinstance(value, str):
        value = value.strip()
        if value:
            return value

    legacy_field = f"guest_{field}"
    legacy_value = getattr(payload, legacy_field, None)
    if isinstance(legacy_value, str):
        legacy_value = legacy_value.strip()
        if legacy_value:
            return legacy_value

    return None


def should_replace_avito_guest_value(
    current_value: str | None,
    incoming_value: str | None,
    placeholder: str | None = "Гость Avito",
) -> bool:
    """Replace only empty or placeholder values with a better Avito contact value."""
    if not isinstance(incoming_value, str):
        return False

    incoming_clean = incoming_value.strip()
    if not incoming_clean:
        return False

    if not isinstance(current_value, str):
        return True

    current_clean = current_value.strip()
    if not current_clean:
        return True

    if placeholder and current_clean == placeholder:
        return True

    return False


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

    @staticmethod
    async def _unblock_avito_dates(booking: Booking):
        """Разблокировка дат в Avito при отмене/удалении брони.
        
        Для Авито-броней ничего не делаем — Авито сам управляет своими датами.
        Для ручных броней — обновляем интервалы доступности.
        """
        try:
            from app.models import BookingSource
            
            # Авито-брони не трогаем — они не блокировались нами через /intervals
            if booking.source == BookingSource.AVITO:
                logger.info(
                    f"Booking #{booking.id} is from Avito — skipping unblock "
                    f"(Avito manages its own dates)"
                )
                return

            # Получаем маппинг house_id -> avito_item_id
            from app.core.config import settings

            item_house_mapping = {}
            for pair in settings.avito_item_ids.split(","):
                if ":" in pair:
                    item_id, house_id = pair.strip().split(":")
                    item_house_mapping[int(house_id)] = int(item_id)

            avito_item_id = item_house_mapping.get(booking.house_id)

            if not avito_item_id:
                logger.info(
                    f"No Avito item ID for house {booking.house_id}, "
                    f"skipping calendar unblock"
                )
                return

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
                    f"⚠️ Failed to unblock Avito dates for booking #{booking.id}"
                )

        except Exception as e:
            logger.error(f"Error unblocking Avito dates: {e}", exc_info=True)
            # Не прерываем отмену/удаление брони при ошибке Avito

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
        """Отмена брони. Каскадно отменяет связанную CleaningTask и
        активные начисления уборки в ledger."""
        try:
            booking = await db.get(Booking, booking_id)
            if not booking:
                return False

            booking.status = BookingStatus.CANCELLED
            booking.updated_at = datetime.now(timezone.utc)

            # C10.2: пропагация в cleaning-домен. Делаем до commit, чтобы
            # отмена брони и каскад были атомарны.
            cleaner_tg_id = await cls._cascade_cancel_cleaning(db, booking_id)

            await db.commit()

            # Разблокировка дат в Avito (вне транзакции, side-effect)
            await cls._unblock_avito_dates(booking)

            # Уведомление уборщицы (best-effort)
            if cleaner_tg_id:
                asyncio.create_task(
                    cls._notify_cleaner_about_cancel(cleaner_tg_id, booking_id)
                )

            # Фоновая синхронизация (safe wrapper)
            asyncio.create_task(cls._safe_background_sheets_sync())

            return True
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}")
            return False

    @staticmethod
    async def _cascade_cancel_cleaning(
        db: AsyncSession, booking_id: int
    ) -> int | None:
        """Находит связанную CleaningTask и переводит её в CANCELLED.
        Активные cleaning_fee ledger-записи также помечаются CANCELLED.
        Возвращает telegram_id уборщицы (если назначена) для уведомления.
        """
        try:
            task_q = await db.execute(
                select(CleaningTask).where(CleaningTask.booking_id == booking_id)
            )
            task = task_q.scalar_one_or_none()
            if not task:
                return None

            terminal = {
                CleaningTaskStatus.DONE,
                CleaningTaskStatus.DECLINED,
                CleaningTaskStatus.CANCELLED,
            }
            now = datetime.now(timezone.utc)

            if task.status not in terminal:
                task.status = CleaningTaskStatus.CANCELLED
                task.updated_at = now

            # Откатываем начисления уборки (если были)
            ledger_q = await db.execute(
                select(CleaningPaymentLedger).where(
                    CleaningPaymentLedger.task_id == task.id,
                    CleaningPaymentLedger.entry_type
                    == CleaningPaymentEntryType.CLEANING_FEE,
                    CleaningPaymentLedger.status != PaymentStatus.CANCELLED,
                )
            )
            for entry in ledger_q.scalars().all():
                entry.status = PaymentStatus.CANCELLED
                entry.comment = (
                    (entry.comment or "")
                    + f" | cancelled: booking #{booking_id} cancelled"
                ).strip()

            # Резолвим telegram_id уборщицы, если она назначена
            cleaner_tg_id: int | None = None
            if task.assigned_to_user_id:
                u_q = await db.execute(
                    select(User.telegram_id).where(User.id == task.assigned_to_user_id)
                )
                cleaner_tg_id = u_q.scalar_one_or_none()

            return cleaner_tg_id

        except Exception as e:
            logger.error(
                f"Error cascading cancel to cleaning for booking {booking_id}: {e}",
                exc_info=True,
            )
            return None

    @staticmethod
    async def _notify_cleaner_about_cancel(cleaner_tg_id: int, booking_id: int):
        """Best-effort уведомление уборщицы об отмене связанной задачи."""
        from app.telegram.bot import bot
        from app.services.notification_service import send_safe

        await send_safe(
            bot, cleaner_tg_id,
            f"ℹ️ Бронь #{booking_id} отменена — связанная уборка снята.",
            context=f"booking_cancel cleaner={cleaner_tg_id}",
        )

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
        db: AsyncSession, booking_payload: AvitoBookingPayload
    ) -> Optional[Booking]:
        """
        Создать или обновить бронь из Avito webhook.
        """
        try:
            from app.models import Booking, BookingSource
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

                incoming_guest_name = extract_avito_contact_value(booking_payload, "name")
                if should_replace_avito_guest_value(existing.guest_name, incoming_guest_name):
                    existing.guest_name = incoming_guest_name
                    existing.updated_at = datetime.now(timezone.utc)

                incoming_guest_phone = extract_avito_contact_value(booking_payload, "phone")
                if should_replace_avito_guest_value(
                    existing.guest_phone,
                    incoming_guest_phone,
                    placeholder=None,
                ):
                    existing.guest_phone = format_phone(incoming_guest_phone)
                    existing.updated_at = datetime.now(timezone.utc)

                # Update other fields if needed ...
                existing.advance_amount = get_prepayment(booking_payload)

                await db.commit()
                await db.refresh(existing)

                # Sync to sheets
                asyncio.create_task(BookingService._safe_background_sheets_sync())

                return existing

            else:
                # Create — but check for overlaps first
                # We need house_id. Since webhook might not contain internal house_id, we need mapping.
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

                check_in = datetime.strptime(booking_payload.check_in, "%Y-%m-%d").date()
                check_out = datetime.strptime(booking_payload.check_out, "%Y-%m-%d").date()

                # Overlap guard
                is_available = await BookingService.check_availability(
                    db, house_id=house_id, check_in=check_in, check_out=check_out
                )
                if not is_available:
                    logger.warning(
                        f"⚠️ OVERLAP BLOCKED: Avito webhook booking {avito_id} "
                        f"({check_in} - {check_out}) conflicts with existing booking "
                        f"for house {house_id}. Skipping creation."
                    )
                    return None

                guest_name = extract_avito_contact_value(booking_payload, "name") or "Гость Avito"
                guest_phone = extract_avito_contact_value(booking_payload, "phone") or ""

                new_booking = Booking(
                    house_id=house_id,
                    guest_name=guest_name,
                    guest_phone=format_phone(guest_phone),
                    check_in=check_in,
                    check_out=check_out,
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

    @staticmethod
    async def confirm_booking(db: AsyncSession, booking_id: int) -> Optional[Booking]:
        """NEW → CONFIRMED transition. Returns the booking or None if not found / wrong state."""
        booking = await db.get(Booking, booking_id)
        if not booking:
            return None
        if booking.status != BookingStatus.NEW:
            return None
        booking.status = BookingStatus.CONFIRMED
        booking.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return booking

    @staticmethod
    async def record_payment(
        db: AsyncSession,
        booking_id: int,
        *,
        full_payment: bool,
        advance_percent: int,
    ) -> tuple[Optional["Booking"], str, bool]:
        """Apply an admin-approved payment (advance or full).

        Returns ``(booking, label, became_paid)`` where:
        - booking is the updated Booking (None if not found)
        - label is the confirmation message to send to the guest
        - became_paid is True when the booking just reached PAID status
        """
        from decimal import Decimal
        from app.services.global_settings import compute_advance_amount

        booking = await db.get(Booking, booking_id)
        if not booking:
            return None, "", False

        total = int(booking.total_price or 0)
        paid = int(booking.advance_amount or 0)
        required_advance = compute_advance_amount(total, advance_percent)

        if full_payment:
            booking.advance_amount = booking.total_price
            booking.status = BookingStatus.PAID
            label = "✅ Оплата подтверждена полностью. Спасибо!"
        else:
            new_advance = min(max(paid, required_advance), total)
            booking.advance_amount = Decimal(str(new_advance))
            if new_advance >= total > 0:
                booking.status = BookingStatus.PAID
                label = "✅ Оплата подтверждена. Спасибо!"
            else:
                booking.status = BookingStatus.CONFIRMED
                remainder = total - new_advance
                label = (
                    f"✅ Задаток ({new_advance:,} ₽) подтверждён.\n"
                    f"Остаток {remainder:,} ₽ — при заселении."
                )

        booking.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return booking, label, booking.status == BookingStatus.PAID
