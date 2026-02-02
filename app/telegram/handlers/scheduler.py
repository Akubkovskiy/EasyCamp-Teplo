"""
Команды управления планировщиком
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.scheduler_service import scheduler_service
from app.core.config import settings

router = Router()


@router.message(Command("scheduler"))
async def scheduler_status(message: Message):
    """Статус планировщика"""

    if not settings.enable_auto_sync:
        await message.answer(
            "⏸ <b>Автосинхронизация отключена</b>\n\n"
            "Включите в настройках:\n"
            "<code>ENABLE_AUTO_SYNC=true</code>",
            parse_mode="HTML",
        )
        return

    jobs = scheduler_service.get_jobs()

    if not jobs:
        await message.answer("⏸ <b>Нет активных задач</b>", parse_mode="HTML")
        return

    status_text = "📅 <b>Статус планировщика</b>\n\n"

    for job in jobs:
        next_run = (
            job.next_run_time.strftime("%H:%M:%S")
            if job.next_run_time
            else "Не запланировано"
        )
        status_text += f"• <b>{job.name}</b>\n"
        status_text += f"  Следующий запуск: {next_run}\n\n"

    status_text += "<b>Настройки:</b>\n"
    status_text += f"• Avito: каждые {settings.avito_sync_interval_minutes} мин\n"
    status_text += f"• Sheets: каждые {settings.sheets_sync_interval_minutes} мин"

    await message.answer(status_text, parse_mode="HTML")


@router.message(Command("scheduler_pause"))
async def pause_scheduler(message: Message):
    """Приостановить планировщик"""
    scheduler_service.pause()
    await message.answer(
        "⏸ <b>Планировщик приостановлен</b>\n\n"
        "Используйте /scheduler_resume для возобновления",
        parse_mode="HTML",
    )


@router.message(Command("scheduler_resume"))
async def resume_scheduler(message: Message):
    """Возобновить планировщик"""
    scheduler_service.resume()
    await message.answer(
        "▶️ <b>Планировщик возобновлен</b>\n\nАвтосинхронизация работает",
        parse_mode="HTML",
    )
