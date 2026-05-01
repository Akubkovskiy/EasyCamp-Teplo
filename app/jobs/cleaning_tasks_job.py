import logging
from datetime import date, datetime, timedelta, timezone

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import and_, select
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus, CleaningTask, User, UserRole
from app.services.cleaning_task_service import CleaningTaskService
from app.telegram.bot import bot
from app.services.notification_service import send_safe

logger = logging.getLogger(__name__)


async def generate_cleaning_tasks_for_tomorrow() -> int:
    """Создать/обновить задачи уборки по выездам на завтра."""
    target = date.today() + timedelta(days=1)
    created = 0

    async with AsyncSessionLocal() as session:
        q = await session.execute(
            select(Booking)
            .options(joinedload(Booking.house))
            .where(
                and_(
                    Booking.check_out == target,
                    Booking.status.in_(
                        [
                            BookingStatus.CONFIRMED,
                            BookingStatus.PAID,
                            BookingStatus.CHECKING_IN,
                            BookingStatus.CHECKED_IN,
                            BookingStatus.COMPLETED,
                        ]
                    ),
                )
            )
        )
        bookings = list(q.scalars().all())

        cleaners_q = await session.execute(select(User).where(User.role == UserRole.CLEANER))
        cleaners = list(cleaners_q.scalars().all())

        for i, b in enumerate(bookings):
            task = await CleaningTaskService.create_task_for_booking(session, b)
            if not task:
                continue

            if task.assigned_to_user_id is None and cleaners:
                # Round-robin по списку уборщиц
                cleaner = cleaners[i % len(cleaners)]
                task.assigned_to_user_id = cleaner.id

            if task.confirm_deadline_at is None:
                base_dt = datetime.combine(target, datetime.min.time()).replace(tzinfo=timezone.utc)
                task.confirm_deadline_at = base_dt + timedelta(minutes=settings.cleaning_confirm_window_min)

            if task.created_at and task.updated_at and task.created_at == task.updated_at:
                created += 1

        await session.commit()

    return created


async def notify_cleaners_about_tasks() -> int:
    """Отправить уборщицам список задач на завтра с переходом в карточку."""
    target = date.today() + timedelta(days=1)
    sent = 0

    async with AsyncSessionLocal() as session:
        cleaners_q = await session.execute(select(User).where(User.role == UserRole.CLEANER))
        cleaners = list(cleaners_q.scalars().all())

        for cleaner in cleaners:
            q = await session.execute(
                select(CleaningTask)
                .where(
                    and_(
                        CleaningTask.scheduled_date == target,
                        CleaningTask.assigned_to_user_id == cleaner.id,
                    )
                )
                .order_by(CleaningTask.id)
            )
            tasks = list(q.scalars().all())
            if not tasks or not cleaner.telegram_id:
                continue

            lines = [f"🧹 Задачи на {target.strftime('%d.%m')}"]
            kb_rows = []
            for t in tasks[:10]:
                lines.append(f"• #{t.id} домик={t.house_id} статус={t.status.value}")
                kb_rows.append([InlineKeyboardButton(text=f"Открыть #{t.id}", callback_data=f"cleaner:task:view:{t.id}")])

            ok = await send_safe(
                bot, cleaner.telegram_id, "\n".join(lines),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
                context=f"cleaning_tasks cleaner={cleaner.id}",
            )
            if ok:
                sent += 1

    return sent


async def run_cleaning_tasks_cycle():
    created = await generate_cleaning_tasks_for_tomorrow()
    sent = await notify_cleaners_about_tasks()
    logger.info("cleaning_tasks_cycle done: created=%s sent=%s", created, sent)
