from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, BookingSource, BookingStatus, House
from app.avito.schemas import AvitoBookingPayload

async def create_or_update_avito_booking(
    session: AsyncSession, 
    payload: AvitoBookingPayload
) -> Booking:
    """
    Создает или обновляет бронь из Avito.
    """
    # 1. Поиск существующей брони по external_id
    stmt = select(Booking).where(Booking.external_id == payload.booking_id)
    result = await session.execute(stmt)
    booking = result.scalar_one_or_none()

    # 2. Маппинг статуса (примерный)
    status_map = {
        "created": BookingStatus.NEW,
        "confirmed": BookingStatus.CONFIRMED,
        "succeeded": BookingStatus.PAID,
        "cancelled": BookingStatus.CANCELLED,
        "rejected": BookingStatus.CANCELLED,
    }
    booking_status = status_map.get(payload.status, BookingStatus.NEW)

    # 3. Поиск или создание домика (заглушка, привязываем к первому или создаем)
    # В реальности нужно маппить item_id из Avito на house_id в нашей БД
    stmt_house = select(House).where(House.name == f"Avito Item {payload.item_id}")
    result_house = await session.execute(stmt_house)
    house = result_house.scalar_one_or_none()
    
    if not house:
        house = House(
            name=f"Avito Item {payload.item_id}", 
            description="Автоматически создан из Avito",
            capacity=4
        )
        session.add(house)
        await session.flush()  # чтобы получить id

    if booking:
        # Обновление
        booking.status = booking_status
        booking.check_in = payload.check_in
        booking.check_out = payload.check_out
        booking.guests_count = payload.guests_count
        booking.total_price = payload.total_price
        booking.guest_name = payload.guest_name
        booking.guest_phone = payload.guest_phone
    else:
        # Создание
        booking = Booking(
            house_id=house.id,
            guest_name=payload.guest_name,
            guest_phone=payload.guest_phone,
            check_in=payload.check_in,
            check_out=payload.check_out,
            guests_count=payload.guests_count,
            total_price=payload.total_price,
            status=booking_status,
            source=BookingSource.AVITO,
            external_id=payload.booking_id,
        )
        session.add(booking)

    await session.commit()
    await session.refresh(booking)
    return booking
