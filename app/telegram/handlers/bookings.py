from datetime import date, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus
from app.core.config import settings
from app.jobs.avito_sync_job import sync_avito_job
from app.services.booking_service import booking_service

router = Router()

@router.message(Command("broni"))
@router.message(F.text.lower().in_(["брони", "бронь", "заезды", "гости"]))
@router.callback_query(F.data == "bookings:menu")
async def show_bookings_menu(event: Message | CallbackQuery):
    """Главное меню броней"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Заезды сегодня", callback_data="bookings:today")],
        [InlineKeyboardButton(text="📆 Заезды на неделю", callback_data="bookings:week")],
        [InlineKeyboardButton(text="📋 Все активные", callback_data="bookings:active")],
        [InlineKeyboardButton(text="🔄 Обновить и открыть таблицу", callback_data="bookings:sync_open")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin:menu")],
    ])
    
    text = "🏕 <b>Управление бронями</b>\n\nЧто хотите посмотреть?"
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "bookings:today")
async def show_today_bookings(callback: CallbackQuery):
    today = date.today()
    await show_bookings_list(callback, start_date=today, end_date=today, title="Заезды сегодня")


@router.callback_query(F.data == "bookings:week")
async def show_week_bookings(callback: CallbackQuery):
    today = date.today()
    week_end = today + timedelta(days=7)
    await show_bookings_list(callback, start_date=today, end_date=week_end, title="Заезды на неделю")


@router.callback_query(F.data == "bookings:active")
async def show_active_bookings(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        stmt = select(Booking).options(joinedload(Booking.house)).where(
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PAID, BookingStatus.NEW]),
            Booking.check_in >= date.today()
        ).order_by(Booking.check_in)
        result = await session.execute(stmt)
        bookings = result.scalars().all()
        
    await send_bookings_response(callback, bookings, "Все активные брони")


from sqlalchemy.orm import joinedload

async def show_bookings_list(callback: CallbackQuery, start_date: date, end_date: date, title: str):
    async with AsyncSessionLocal() as session:
        stmt = select(Booking).options(joinedload(Booking.house)).where(
            Booking.check_in >= start_date,
            Booking.check_in <= end_date
        ).order_by(Booking.check_in)
        result = await session.execute(stmt)
        bookings = result.scalars().all()
        
    await send_bookings_response(callback, bookings, title)


async def send_bookings_response(callback: CallbackQuery, bookings: list[Booking], title: str):
    """Отправка списка броней с кнопками управления"""
    
    if not bookings:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к бронированиям", callback_data="bookings:menu")]
        ])
        await callback.message.edit_text(
            f"<b>{title}</b>\n\nНет броней за этот период 🤷‍♂️",
            reply_markup=keyboard
        )
        await callback.answer()
        return

    # Формируем текст списка
    text = f"<b>{title} ({len(bookings)})</b>\n\n"
    
    status_emoji = {
        BookingStatus.NEW: "🆕",
        BookingStatus.CONFIRMED: "✅",
        BookingStatus.PAID: "💰",
        BookingStatus.CANCELLED: "❌",
        BookingStatus.COMPLETED: "🏁",
    }

    # Создаем кнопки для каждой брони (макс 10 на страницу для удобства)
    buttons = []
    current_row = []
    
    for b in bookings:
        text += (
            f"#{b.id} {status_emoji.get(b.status, '❓')} <b>{b.check_in.strftime('%d.%m')} - {b.check_out.strftime('%d.%m')}</b>\n"
            f"🏠 {b.house.name} | 👤 {b.guest_name}\n"
            f"💰 {b.total_price:,.0f} ₽\n"
            f"──────────────────\n"
        )
        
        # Добавляем кнопку с ID
        current_row.append(InlineKeyboardButton(text=f"#{b.id}", callback_data=f"booking:view:{b.id}"))
        
        if len(current_row) == 5: # 5 кнопок в ряд
            buttons.append(current_row)
            current_row = []
            
    if current_row:
        buttons.append(current_row)
        
    # Кнопка назад
    buttons.append([InlineKeyboardButton(text="🔙 Назад к меню броней", callback_data="bookings:menu")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "bookings:sync_open")
async def sync_and_open_table(callback: CallbackQuery):
    """Синхронизация с Авито и открытие таблицы"""
    
    # Редактируем сообщение, показывая статус
    await callback.message.edit_text("⏳ <b>Синхронизируем данные с Avito...</b>", parse_mode="HTML")
    
    # 1. Синхронизация с Avito (получение новых броней)
    await sync_avito_job()
    
    # 2. Обновление статуса
    await callback.message.edit_text("⏳ <b>Обновляем Google Sheets...</b>", parse_mode="HTML")
    
    # 3. Принудительная синхронизация таблицы
    # Используем to_thread т.к. sync_bookings_to_sheet синхронная, но вызываем через сервис для правильности
    from app.services.sheets_service import sheets_service
    import asyncio
    
    # Получаем актуальные брони для таблицы
    async with AsyncSessionLocal() as session:
        stmt = select(Booking).options(joinedload(Booking.house)).order_by(Booking.check_in)
        result = await session.execute(stmt)
        bookings = result.scalars().all()
    
    # Отправляем в GS
    try:
        await asyncio.to_thread(sheets_service.sync_bookings_to_sheet, bookings)
        status_text = "✅ <b>Синхронизация завершена!</b>\n\nДанные актуализированы."
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        # Логируем ошибку, но не отправляем юзеру страшный текст, если это не invalid_grant
        if "invalid_grant" in str(e):
            status_text = (
                "⚠️ <b>Ошибка доступа к Google Таблице!</b>\n\n"
                "Система не может обновить таблицу. Возможно, устарели ключи доступа или удален сервисный аккаунт.\n"
                "Синхронизация с Avito прошла успешно, но таблица не обновлена."
            )
        else:
            status_text = (
                f"⚠️ <b>Ошибка при обновлении таблицы!</b>\n\n"
                f"Синхронизация с Avito прошла, но таблицу обновить не удалось.\n"
                f"Детали ошибки: {str(e)}"
            )
        # Логируем в консоль для админа
        print(f"Sheets Sync Error: {error_details}")
    
    # 4. Финиш - даем ссылку
    sheet_link = f"https://docs.google.com/spreadsheets/d/{settings.google_sheets_spreadsheet_id}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Перейти в таблицу", url=sheet_link)],
        [InlineKeyboardButton(text="🔙 К списку броней", callback_data="bookings:menu")]
    ])
    
    await callback.message.edit_text(
        status_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()
