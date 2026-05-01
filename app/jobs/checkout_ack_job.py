"""
Checkout acknowledgment notification jobs.

Escalation chain for tomorrow's checkouts:
  12:00 — send reminder with ack buttons (pending:0)
  13:00 — re-send if still pending:0 (→ pending:1)
  14:00 — alert admin if still pending:1

Plus:
  09:00 — non-interactive morning briefing for today's checkouts (guest phone included)
"""
import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus, User, UserRole
from app.services.checkout_ack import checkout_ack_keyboard, get_ack_status, set_ack_status

logger = logging.getLogger(__name__)

_ACTIVE = [
    BookingStatus.CONFIRMED,
    BookingStatus.PAID,
    BookingStatus.CHECKING_IN,
    BookingStatus.CHECKED_IN,
]


async def _bookings_on(session, target: date) -> list[Booking]:
    q = await session.execute(
        select(Booking)
        .options(joinedload(Booking.house))
        .where(Booking.check_out == target, Booking.status.in_(_ACTIVE))
    )
    return list(q.unique().scalars().all())


async def _cleaners(session) -> list[User]:
    q = await session.execute(select(User).where(User.role == UserRole.CLEANER))
    return list(q.scalars().all())


async def send_checkout_ack_reminders():
    """12:00: send day-before reminder with ack buttons for tomorrow's checkouts."""
    from app.telegram.bot import bot

    tomorrow = date.today() + timedelta(days=1)
    async with AsyncSessionLocal() as session:
        bookings = await _bookings_on(session, tomorrow)
        cleaners = await _cleaners(session)
        if not bookings or not cleaners:
            return

        for b in bookings:
            ack = await get_ack_status(session, b.id)
            if ack in ("acked", "declined"):
                continue  # pre-accepted from week view or already handled

            house = b.house.name if b.house else f"Дом {b.house_id}"
            text = (
                f"🔔 <b>Завтра выезд!</b>\n\n"
                f"🏠 {house}\n"
                f"📅 {b.check_in.strftime('%d.%m')} → {b.check_out.strftime('%d.%m')}\n"
                f"👥 {b.guests_count} чел.\n\n"
                "Подтвердите, что примете уборку."
            )
            kb = checkout_ack_keyboard(b.id)
            for c in cleaners:
                try:
                    await bot.send_message(c.telegram_id, text, reply_markup=kb, parse_mode="HTML")
                except Exception as e:
                    logger.warning(f"ack reminder → cleaner {c.telegram_id}: {e}")

            await set_ack_status(session, b.id, "pending:0")
            logger.info(f"Checkout ack reminder sent for booking {b.id} (checkout {tomorrow})")


async def retry_checkout_ack():
    """13:00: re-send reminder for bookings still at pending:0."""
    from app.telegram.bot import bot

    tomorrow = date.today() + timedelta(days=1)
    async with AsyncSessionLocal() as session:
        bookings = await _bookings_on(session, tomorrow)
        cleaners = await _cleaners(session)
        if not bookings or not cleaners:
            return

        for b in bookings:
            if await get_ack_status(session, b.id) != "pending:0":
                continue

            house = b.house.name if b.house else f"Дом {b.house_id}"
            text = (
                f"⏰ <b>Напоминание: завтра выезд!</b>\n\n"
                f"🏠 {house}\n"
                f"📅 {b.check_in.strftime('%d.%m')} → {b.check_out.strftime('%d.%m')}\n"
                f"👥 {b.guests_count} чел.\n\n"
                "Вы ещё не подтвердили уборку."
            )
            kb = checkout_ack_keyboard(b.id)
            for c in cleaners:
                try:
                    await bot.send_message(c.telegram_id, text, reply_markup=kb, parse_mode="HTML")
                except Exception as e:
                    logger.warning(f"ack retry → cleaner {c.telegram_id}: {e}")

            await set_ack_status(session, b.id, "pending:1")
            logger.info(f"Checkout ack retry sent for booking {b.id}")


async def alert_admin_no_ack():
    """14:00: alert admin if booking still at pending:1 (2 reminders sent, no response)."""
    from app.telegram.bot import bot
    from app.core.config import settings

    tomorrow = date.today() + timedelta(days=1)
    async with AsyncSessionLocal() as session:
        bookings = await _bookings_on(session, tomorrow)
        if not bookings:
            return

        for b in bookings:
            if await get_ack_status(session, b.id) != "pending:1":
                continue

            house = b.house.name if b.house else f"Дом {b.house_id}"
            text = (
                f"⚠️ <b>Уборщица не ответила!</b>\n\n"
                f"🏠 {house}\n"
                f"📅 Выезд: {b.check_out.strftime('%d.%m')}\n\n"
                "Никто не подтвердил уборку. Требуется ручное управление."
            )
            try:
                await bot.send_message(settings.telegram_chat_id, text, parse_mode="HTML")
                logger.warning(f"Admin alerted: no ack for booking {b.id}")
            except Exception as e:
                logger.error(f"Failed to alert admin for booking {b.id}: {e}")


async def send_morning_checkout_briefing():
    """09:00: non-interactive morning briefing for today's checkouts with guest phone."""
    from app.telegram.bot import bot

    today = date.today()
    async with AsyncSessionLocal() as session:
        bookings = await _bookings_on(session, today)
        cleaners = await _cleaners(session)
        if not bookings or not cleaners:
            return

        for b in bookings:
            house = b.house.name if b.house else f"Дом {b.house_id}"
            text = (
                f"🌅 <b>Сегодня выезд</b>\n\n"
                f"🏠 {house}\n"
                f"📅 {b.check_in.strftime('%d.%m')} → {b.check_out.strftime('%d.%m')}\n"
                f"👥 {b.guests_count} чел.\n"
                f"📞 {b.guest_phone}\n\n"
                "Гость выезжает до 12:00 🧹"
            )
            for c in cleaners:
                try:
                    await bot.send_message(c.telegram_id, text, parse_mode="HTML")
                except Exception as e:
                    logger.warning(f"morning briefing → cleaner {c.telegram_id}: {e}")

        logger.info(f"Morning checkout briefing: {len(bookings)} booking(s) on {today}")

        # Cleanup stale ack keys for past checkouts
        await _cleanup_stale_ack_keys(session, today)


async def _cleanup_stale_ack_keys(session, today: date) -> None:
    from sqlalchemy import select as sa_select
    from app.models import GlobalSetting

    try:
        q = await session.execute(
            sa_select(GlobalSetting).where(GlobalSetting.key.like("ack_checkout_%"))
        )
        stale = []
        for gs in q.scalars().all():
            try:
                bid = int(gs.key.replace("ack_checkout_", ""))
                booking = await session.get(Booking, bid)
                if booking and booking.check_out < today:
                    stale.append(gs)
            except (ValueError, Exception):
                pass

        for gs in stale:
            await session.delete(gs)
        if stale:
            await session.commit()
            logger.info(f"Cleaned up {len(stale)} stale ack key(s)")
    except Exception as e:
        logger.warning(f"Ack cleanup failed: {e}")
