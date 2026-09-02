"""
Синхронизация броней из Яндекс Путешествий в локальную БД.

Паттерн аналогичен avito_sync_service: получаем заказы → создаём/обновляем Booking.
Polling (не webhooks) — Яндекс Travel API не поддерживает push-уведомления.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Booking, BookingSource, BookingStatus, House
from app.schemas.booking import BookingCreate
from app.services.booking_service import BookingService
from app.services.yandex_travel_api_service import yandex_travel_api_service
from app.yandex_travel.schemas import YaTrOrder, parse_order

logger = logging.getLogger(__name__)


def _map_yatr_status(status: Optional[str]) -> BookingStatus:
    """Маппинг статуса заказа Яндекс → внутренний BookingStatus."""
    mapping: Dict[str, BookingStatus] = {
        "pending":    BookingStatus.NEW,
        "confirmed":  BookingStatus.CONFIRMED,
        "paid":       BookingStatus.PAID,
        "cancelled":  BookingStatus.CANCELLED,
        "canceled":   BookingStatus.CANCELLED,
        "completed":  BookingStatus.COMPLETED,
    }
    return mapping.get((status or "").lower(), BookingStatus.NEW)


def _external_id(order: YaTrOrder) -> str:
    return f"yatr:{order.order_id}"


async def _find_house_for_order(
    db: AsyncSession, order: YaTrOrder, hotel_room_mapping: Dict[str, int]
) -> Optional[int]:
    """
    Определить house_id по hotel_id+room_id из YANDEX_TRAVEL_ROOM_IDS маппинга.

    Формат переменной: "hotel_id/room_id:house_id,hotel_id/room_id:house_id"
    """
    key = f"{order.hotel_id}/{order.room_id}"
    house_id = hotel_room_mapping.get(key) or hotel_room_mapping.get(order.room_id or "")
    if not house_id:
        logger.error(
            "YaTr rejected order %s: no stable house mapping for hotel=%s room=%s",
            order.order_id,
            order.hotel_id,
            order.room_id,
        )
        return None

    house = await db.get(House, house_id)
    if house is None:
        logger.error(
            "YaTr rejected order %s: mapped house_id=%s does not exist",
            order.order_id,
            house_id,
        )
        return None
    return house.id


async def process_yatr_order(
    db: AsyncSession,
    order: YaTrOrder,
    hotel_room_mapping: Dict[str, int],
) -> Optional[Booking]:
    """Создать или обновить бронь по заказу из Яндекс Путешествий."""
    if not order.order_id:
        logger.warning("YaTr: заказ без order_id, пропускаем")
        return None

    ext_id = _external_id(order)

    # Ищем существующую бронь
    result = await db.execute(
        select(Booking).where(
            Booking.external_id == ext_id,
            Booking.source == BookingSource.YANDEX_TRAVEL,
        )
    )
    existing: Optional[Booking] = result.scalar_one_or_none()

    new_status = _map_yatr_status(order.status)

    if existing:
        # Обновляем только если статус изменился
        if existing.status == new_status:
            return existing
        logger.info("YaTr: обновляем бронь %s: %s → %s", ext_id, existing.status, new_status)
        existing.status = new_status
        existing.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing

    # Создаём новую бронь
    if not order.check_in or not order.check_out:
        logger.warning("YaTr: заказ %s без дат, пропускаем", order.order_id)
        return None
    if order.check_out <= order.check_in:
        logger.error(
            "YaTr rejected order %s: check_out=%s must be after check_in=%s",
            order.order_id,
            order.check_out,
            order.check_in,
        )
        return None

    house_id = await _find_house_for_order(db, order, hotel_room_mapping)
    if house_id is None:
        return None

    create = BookingCreate(
        house_id=house_id,
        guest_name=order.guest.name if order.guest else "Гость (Яндекс)",
        guest_phone=order.guest.phone if order.guest else "",
        check_in=order.check_in,
        check_out=order.check_out,
        guests_count=order.guests_count or 1,
        total_price=Decimal(str(order.total_price or 0)),
        advance_amount=Decimal("0"),
        commission=Decimal("0"),
        prepayment_owner=Decimal("0"),
        status=new_status,
        source=BookingSource.YANDEX_TRAVEL,
        external_id=ext_id,
    )
    result = await BookingService.create_booking_result(db, create)
    if result.created and result.booking:
        logger.info("YaTr: создана бронь #%d (order %s)", result.booking.id, order.order_id)
        return result.booking
    if result.duplicate and result.booking:
        logger.info("YaTr: duplicate order %s resolved to booking #%d", order.order_id, result.booking.id)
        return result.booking

    logger.error(
        "YaTr rejected order %s before insert: %s",
        order.order_id,
        result.reason or "unknown_error",
    )
    return None


def parse_hotel_room_mapping() -> Dict[str, int]:
    """
    Разбирает YANDEX_TRAVEL_ROOM_IDS в словарь.

    Формат: "hotel_id/room_id:house_id,hotel_id/room_id:house_id"
    Пример: "YA1234/ROOM1:1,YA1234/ROOM2:2"
    """
    mapping: Dict[str, int] = {}
    raw = (settings.yandex_travel_room_ids or "").strip()
    if not raw:
        return mapping
    for pair in raw.split(","):
        pair = pair.strip()
        if ":" not in pair:
            continue
        key, house_id_str = pair.rsplit(":", 1)
        try:
            mapping[key.strip()] = int(house_id_str.strip())
        except ValueError:
            logger.warning("YaTr: неверный маппинг: %s", pair)
    return mapping


async def sync_yatr_orders(
    db: AsyncSession,
    since: Optional[datetime] = None,
) -> Dict[str, List[Any]]:
    """
    Основная функция синхронизации.

    Возвращает словарь:
    {
        "new_bookings": [...],
        "updated_bookings": [...],
        "errors": [...],
        "total": int,
    }
    """
    hotel_room_mapping = parse_hotel_room_mapping()

    # Период polling: от (now - интервал) до сейчас
    if since is None:
        interval = settings.yandex_travel_sync_interval_minutes
        since = datetime.utcnow() - timedelta(minutes=interval + 5)  # +5 мин буфер

    logger.info("YaTr: sync orders modified since %s", since)

    raw_orders = yandex_travel_api_service.get_orders_modified_since(since)
    logger.info("YaTr: получено %d заказов", len(raw_orders))

    new_bookings: List[Booking] = []
    updated_bookings: List[Booking] = []
    errors: List[str] = []

    for raw in raw_orders:
        try:
            order = parse_order(raw)
            ext_id = _external_id(order)

            # Проверяем: существует уже?
            result = await db.execute(
                select(Booking).where(
                    Booking.external_id == ext_id,
                    Booking.source == BookingSource.YANDEX_TRAVEL,
                )
            )
            existed = result.scalar_one_or_none() is not None

            booking = await process_yatr_order(db, order, hotel_room_mapping)
            if booking is None:
                continue

            if existed:
                updated_bookings.append(booking)
            else:
                new_bookings.append(booking)

        except Exception as e:
            logger.error("YaTr: ошибка обработки заказа %s: %s", raw.get("order_id", "?"), e, exc_info=True)
            errors.append(str(e))

    return {
        "new_bookings": new_bookings,
        "updated_bookings": updated_bookings,
        "errors": errors,
        "total": len(raw_orders),
    }
