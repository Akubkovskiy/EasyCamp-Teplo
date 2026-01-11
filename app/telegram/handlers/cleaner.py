from datetime import date, datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, or_, and_

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus
from app.telegram.auth.admin import get_user_name

router = Router()


async def get_cleaning_schedule(start_date: date, end_date: date) -> list[Booking]:
    """Получает список броней, у которых выезд в заданном диапазоне"""
    async with AsyncSessionLocal() as session:
        query = select(Booking).where(
            and_(
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PAID, BookingStatus.COMPLETED]),
                Booking.check_out >= start_date,
                Booking.check_out <= end_date
            )
        ).order_by(Booking.check_out)
        
        result = await session.execute(query)
        bookings = result.scalars().all()
        return list(bookings)


async def get_nearest_checkouts() -> str:
    """Формирует строку с ближайшими выездами по домам"""
    today = date.today()
    
    async with AsyncSessionLocal() as session:
        # Ищем ближайший выезд для каждого дома
        # Для простоты берем все выезды на неделю вперед
        prospect_date = today + timedelta(days=7)
        
        query = select(Booking).where(
            and_(
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PAID, BookingStatus.COMPLETED]),
                Booking.check_out >= today,
                Booking.check_out <= prospect_date
            )
        ).order_by(Booking.check_out)
        
        result = await session.execute(query)
        bookings = list(result.scalars().all())
    
    if not bookings:
        return "Нет выездов на ближайшую неделю."
    
    # Группируем по датам, чтобы найти ближайшую уникальную дату выезда
    summary_lines = []
    
    # Сделаем просто список ближайших 3-5 выездов
    seen_houses = set()
    count = 0
    
    for b in bookings:
        if b.house_id in seen_houses:
            continue
            
        summary_lines.append(f"{b.house.name} ({b.check_out.strftime('%d.%m')})")
        seen_houses.add(b.house_id)
        count += 1
        if count >= 3: # Показываем макс 3 дома в саммари
            break
            
    return ", ".join(summary_lines)


def get_cleaner_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="cleaner:schedule:today"),
            InlineKeyboardButton(text="📅 Завтра", callback_data="cleaner:schedule:tomorrow"),
        ],
        [InlineKeyboardButton(text="🗓 На неделю", callback_data="cleaner:schedule:week")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="cleaner:menu")],
    ])


@router.callback_query(F.data == "cleaner:menu")
async def cleaner_menu_callback(callback: CallbackQuery):
    await show_cleaner_menu(callback.message, callback.from_user.id)
    await callback.answer()


async def show_cleaner_menu(message: Message, user_id: int):
    """Главное меню уборщицы"""
    name = await get_user_name(user_id) or message.chat.first_name or "друг"
    
    nearest_summary = await get_nearest_checkouts()
    
    text = (
        f"👋 <b>Добрый день, {name}!</b>\n\n"
        f"🧹 <b>Ближайшие выезды:</b>\n"
        f"{nearest_summary}\n\n"
        "Выберите период для просмотра графика:"
    )
    
    if isinstance(message, Message):
        await message.answer(text, reply_markup=get_cleaner_keyboard())
    elif hasattr(message, 'edit_text'): # Если передали message из callback
        await message.edit_text(text, reply_markup=get_cleaner_keyboard())


@router.callback_query(F.data.startswith("cleaner:schedule:"))
async def show_schedule(callback: CallbackQuery):
    """Показать график уборок"""
    mode = callback.data.split(":")[2]
    today = date.today()
    
    if mode == "today":
        start = today
        end = today
        title = "на СЕГОДНЯ"
    elif mode == "tomorrow":
        start = today + timedelta(days=1)
        end = today + timedelta(days=1)
        title = "на ЗАВТРА"
    else: # week
        start = today
        end = today + timedelta(days=7)
        title = "на НЕДЕЛЮ"
        
    bookings = await get_cleaning_schedule(start, end)
    
    if not bookings:
        await callback.message.edit_text(
            f"🧹 <b>График уборок {title}</b>\n\n"
            "✅ Выездов нет, можно отдыхать!",
            reply_markup=get_cleaner_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = f"🧹 <b>График уборок {title}</b>\n\n"
    
    days_map = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
    
    # Группировка по датам для красоты
    current_date = None
    
    for b in bookings:
        # Проверяем не изменилась ли дата (для недельного вида)
        if b.check_out != current_date:
            current_date = b.check_out
            weekday = days_map[current_date.weekday()]
            text += f"\n📅 <b>{current_date.strftime('%d.%m')} ({weekday})</b>\n"
            
        text += (
            f"   🏠 <b>{b.house.name}</b> | 👥 {b.guests_count} чел\n"
            f"   📞 {b.guest_phone}\n"
            f"   🕒 Выезд до 12:00\n" 
        )

    await callback.message.edit_text(
        text, 
        reply_markup=get_cleaner_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
