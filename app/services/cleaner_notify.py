"""Event-based cleaner notifications: fires when a booking is confirmed/paid and check-in is soon."""
import logging
from datetime import date, timedelta

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import User, UserRole

logger = logging.getLogger(__name__)

NOTIFY_WITHIN_DAYS = 7


async def notify_cleaners_new_booking(bot, booking) -> None:
    """Notify all cleaners when a booking is confirmed/paid and check-in is within 7 days."""
    today = date.today()
    check_in = booking.check_in if hasattr(booking.check_in, "year") else booking.check_in
    if check_in > today + timedelta(days=NOTIFY_WITHIN_DAYS):
        return

    async with AsyncSessionLocal() as s:
        cleaners_q = await s.execute(select(User).where(User.role == UserRole.CLEANER))
        cleaners = list(cleaners_q.scalars().all())
        if not cleaners:
            return
        if booking.house_id:
            from app.models import House
            house = await s.get(House, booking.house_id)
            house_name = house.name if house else f"Дом {booking.house_id}"
        else:
            house_name = "—"

    check_out = booking.check_out
    days_until = (check_in - today).days
    when = "сегодня" if days_until == 0 else f"через {days_until} дн." if days_until > 0 else "уже заехали"

    text = (
        f"🔔 <b>Новая бронь подтверждена</b>\n\n"
        f"🏠 {house_name}\n"
        f"📅 {check_in.strftime('%d.%m')} → {check_out.strftime('%d.%m')}\n"
        f"👥 {booking.guests_count} чел.\n"
        f"📌 Заезд {when}"
    )

    for cleaner in cleaners:
        try:
            await bot.send_message(cleaner.telegram_id, text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Failed to notify cleaner {cleaner.telegram_id}: {e}")
