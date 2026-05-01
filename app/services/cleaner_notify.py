"""Event-based cleaner notifications."""
import logging
from datetime import date, timedelta

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import House, User, UserRole

logger = logging.getLogger(__name__)

NOTIFY_WITHIN_DAYS = 7


async def _get_cleaners_and_house(booking) -> tuple[list, str]:
    async with AsyncSessionLocal() as s:
        cleaners_q = await s.execute(select(User).where(User.role == UserRole.CLEANER))
        cleaners = list(cleaners_q.scalars().all())
        house = await s.get(House, booking.house_id) if booking.house_id else None
        house_name = house.name if house else f"Дом {booking.house_id}"
    return cleaners, house_name


async def notify_cleaners_new_booking(bot, booking) -> None:
    """Notify cleaners when a PAID booking has check-in within 7 days.
    For Avito bookings (already CONFIRMED) also fires since payment is external."""
    today = date.today()
    check_in = booking.check_in
    if check_in > today + timedelta(days=NOTIFY_WITHIN_DAYS):
        return

    cleaners, house_name = await _get_cleaners_and_house(booking)
    if not cleaners:
        return

    days_until = (check_in - today).days
    when = "сегодня" if days_until == 0 else f"через {days_until} дн." if days_until > 0 else "уже заехали"

    text = (
        f"🔔 <b>Новая бронь оплачена</b>\n\n"
        f"🏠 {house_name}\n"
        f"📅 {check_in.strftime('%d.%m')} → {booking.check_out.strftime('%d.%m')}\n"
        f"👥 {booking.guests_count} чел.\n"
        f"📌 Заезд {when}"
    )

    for cleaner in cleaners:
        try:
            await bot.send_message(cleaner.telegram_id, text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Failed to notify cleaner {cleaner.telegram_id}: {e}")


async def notify_cleaners_booking_cancelled(bot, booking) -> None:
    """Notify all cleaners when a booking is cancelled (so they can update their schedule)."""
    today = date.today()
    # Only relevant if checkout is in the future (otherwise they don't need to know)
    if booking.check_out < today:
        return

    cleaners, house_name = await _get_cleaners_and_house(booking)
    if not cleaners:
        return

    text = (
        f"❌ <b>Бронь отменена</b>\n\n"
        f"🏠 {house_name}\n"
        f"📅 {booking.check_in.strftime('%d.%m')} → {booking.check_out.strftime('%d.%m')}\n"
        f"👥 {booking.guests_count} чел."
    )

    for cleaner in cleaners:
        try:
            await bot.send_message(cleaner.telegram_id, text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Failed to notify cleaner {cleaner.telegram_id}: {e}")
