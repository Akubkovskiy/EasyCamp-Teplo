"""Sends advance checkout reminders to cleaners based on their personal notify_days setting."""
import logging
from datetime import date, timedelta

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus, GlobalSetting, User, UserRole
from app.services.notification_service import send_safe

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = [
    BookingStatus.CONFIRMED,
    BookingStatus.PAID,
    BookingStatus.CHECKING_IN,
    BookingStatus.CHECKED_IN,
]


async def send_advance_checkout_notifications():
    """For each cleaner reads their notify_days setting and sends reminders for matching checkouts."""
    from app.telegram.bot import bot

    today = date.today()

    async with AsyncSessionLocal() as s:
        cleaners_q = await s.execute(select(User).where(User.role == UserRole.CLEANER))
        cleaners = list(cleaners_q.scalars().all())

        if not cleaners:
            return

        for cleaner in cleaners:
            setting = await s.get(GlobalSetting, f"cleaner_notify_days_{cleaner.id}")
            notify_days = 0  # off by default; cleaner can enable in Settings
            if setting and setting.value:
                try:
                    notify_days = int(setting.value)
                except ValueError:
                    pass

            if notify_days == 0:
                continue

            target_date = today + timedelta(days=notify_days)

            bookings_q = await s.execute(
                select(Booking).where(
                    Booking.check_out == target_date,
                    Booking.status.in_(ACTIVE_STATUSES),
                )
            )
            bookings = list(bookings_q.scalars().all())

            if not bookings:
                continue

            days_word = _days_word(notify_days)
            lines = [
                f"🔔 <b>Напоминание: выезд через {notify_days} {days_word}</b>\n"
                f"📅 {target_date.strftime('%d.%m.%Y')}\n"
            ]
            for b in bookings:
                house_name = b.house.name if hasattr(b, "house") and b.house else f"Дом {b.house_id}"
                lines.append(f"🏠 {house_name} — {b.guests_count} гост.")

            lines.append("\nПодготовьтесь заранее 🧹")
            text = "\n".join(lines)

            ok = await send_safe(bot, cleaner.telegram_id, text, context=f"advance_reminder cleaner={cleaner.id}")
            if ok:
                logger.info(
                    f"Advance checkout reminder sent to cleaner {cleaner.telegram_id} "
                    f"for {target_date} ({len(bookings)} bookings)"
                )


def _days_word(n: int) -> str:
    if n == 1:
        return "день"
    if 2 <= n <= 4:
        return "дня"
    return "дней"
