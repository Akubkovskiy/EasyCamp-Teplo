"""
Обработчики для синхронизации с Google Sheets
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import AsyncSessionLocal
from app.models import Booking
from app.services.sheets_service import sheets_service
from app.core.config import settings

router = Router()


@router.message(Command("sync"))
async def sync_to_sheets(message: Message):
    """Синхронизировать данные с Google Sheets"""

    await message.answer("🔄 Начинаю синхронизацию с Google Sheets...")

    try:
        # Получаем все брони из БД
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Booking)
                .options(joinedload(Booking.house))
                .order_by(Booking.check_in)
            )
            result = await session.execute(stmt)
            bookings = result.scalars().all()

        # Синхронизируем с Google Sheets
        sheets_service.sync_bookings_to_sheet(bookings)
        sheets_service.create_dashboard(bookings)

        await message.answer(
            f"✅ <b>Синхронизация завершена!</b>\n\n"
            f"📊 Обновлено броней: {len(bookings)}\n"
            f"📋 Листы: Все брони, Dashboard\n\n"
            f"Используйте /sheet для получения ссылки на таблицу"
        )

    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка синхронизации:</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Проверьте:\n"
            f"• Файл google-credentials.json в корне проекта\n"
            f"• ID таблицы в .env\n"
            f"• Доступ Service Account к таблице"
        )


@router.message(Command("sheet"))
async def get_sheet_link(message: Message):
    """Получить ссылку на Google таблицу"""

    spreadsheet_id = settings.google_sheets_spreadsheet_id

    if not spreadsheet_id:
        await message.answer(
            "❌ ID таблицы не настроен\n\nДобавьте GOOGLE_SHEETS_SPREADSHEET_ID в .env"
        )
        return

    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

    await message.answer(
        f"📊 <b>Google Таблица с бронями</b>\n\n"
        f"🔗 <a href='{url}'>Открыть таблицу</a>\n\n"
        f"Используйте /sync для обновления данных"
    )
