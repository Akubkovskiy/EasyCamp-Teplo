import logging
from datetime import datetime, timezone

from sqlalchemy import and_, select

from app.core.config import settings
from app.database import AsyncSessionLocal
from app.models import CleaningTask, CleaningTaskStatus, User, UserRole
from app.telegram.bot import bot

logger = logging.getLogger(__name__)


async def run_cleaning_sla_monitor():
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        q = await session.execute(
            select(CleaningTask).where(
                and_(
                    CleaningTask.status == CleaningTaskStatus.PENDING,
                    CleaningTask.confirm_deadline_at.is_not(None),
                    CleaningTask.confirm_deadline_at < now,
                )
            )
        )
        overdue = list(q.scalars().all())
        if not overdue:
            return

        admin_q = await session.execute(select(User).where(User.role.in_([UserRole.ADMIN, UserRole.OWNER])))
        admins = [u.telegram_id for u in admin_q.scalars().all() if u.telegram_id]
        if settings.telegram_chat_id not in admins:
            admins.append(settings.telegram_chat_id)

        for task in overdue:
            task.status = CleaningTaskStatus.ESCALATED
            task.escalated_at = now
            task.updated_at = now

            text = (
                f"🚨 SLA Escalation: задача уборки #{task.id}\n"
                f"Домик: {task.house_id}\n"
                f"Дата: {task.scheduled_date.strftime('%d.%m.%Y')}\n"
                f"Дедлайн подтверждения истёк"
            )
            for aid in admins:
                try:
                    await bot.send_message(aid, text)
                except Exception:
                    pass

        await session.commit()
        logger.warning("Escalated overdue cleaning tasks: %s", len(overdue))
