from datetime import date, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus

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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к бронированиям", callback_data="bookings:menu")]
    ])
    
    if not bookings:
        await callback.message.edit_text(
            f"<b>{title}</b>\n\nНет броней за этот период 🤷‍♂️",
            reply_markup=keyboard
        )
        await callback.answer()
        return

    text = f"<b>{title} ({len(bookings)})</b>\n\n"
    
    status_emoji = {
        BookingStatus.NEW: "🆕",
        BookingStatus.CONFIRMED: "✅",
        BookingStatus.PAID: "💰",
        BookingStatus.CANCELLED: "❌",
        BookingStatus.COMPLETED: "🏁",
    }

    for b in bookings:
        text += (
            f"{status_emoji.get(b.status, '❓')} <b>{b.check_in.strftime('%d.%m')} - {b.check_out.strftime('%d.%m')}</b>\n"
            f"🏠 {b.house.name}\n"
            f"👤 {b.guest_name} ({b.guests_count} чел.)\n"
            f"📞 {b.guest_phone}\n"
            f"💰 {b.total_price:,.0f} ₽\n"
            f"──────────────────\n"
        )
        
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
