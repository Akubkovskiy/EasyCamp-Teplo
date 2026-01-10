import datetime
import logging

from aiogram import Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from app.services.booking_service import booking_service

from app.telegram.ui.calendar import build_month_keyboard, month_title
from app.telegram.state.availability import (
    availability_states,
    AvailabilityState,
)

router = Router()
logger = logging.getLogger(__name__)


from app.telegram.auth.admin import is_admin

@router.message(Command("availability"))
async def availability_command(message: Message):
    """Обработчик команды /availability для проверки доступности домиков"""
    if message.from_user is None:
        return

    user_id = message.from_user.id
    today = datetime.date.today()

    availability_states[user_id] = AvailabilityState()

    await message.answer(
        "📅 <b>Выберите дату заезда</b>",
        reply_markup=build_month_keyboard(
            today.year,
            today.month,
            prefix="checkin",
            min_date=today,
        ),
    )

@router.callback_query(lambda c: c.data in ["admin:availability", "guest:availability"])
async def start_availability(callback: CallbackQuery):
    if callback.from_user is None or callback.message is None:
        return

    user_id = callback.from_user.id
    today = datetime.date.today()

    availability_states[user_id] = AvailabilityState()

    await callback.message.edit_text(
        "📅 <b>Выберите дату заезда</b>",
        reply_markup=build_month_keyboard(
            today.year,
            today.month,
            prefix="checkin",
            min_date=today,
        ),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("checkin_month:"))
async def change_checkin_month(callback: CallbackQuery):
    if callback.data is None or callback.message is None:
        return

    _, value = callback.data.split(":")
    year, month = map(int, value.split("-"))

    await callback.message.edit_text(
        "📅 <b>Выберите дату заезда</b>",
        reply_markup=build_month_keyboard(
            year,
            month,
            prefix="checkin",
        ),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("checkin_pick_month:"))
async def start_pick_month(callback: CallbackQuery):
    if callback.data is None or callback.message is None:
        return
        
    _, year = callback.data.split(":")
    from app.telegram.ui.calendar import build_year_keyboard
    
    await callback.message.edit_text(
        f"📅 <b>Выберите месяц ({year})</b>",
        reply_markup=build_year_keyboard(int(year), prefix="checkin"),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("checkin_pick_year:"))
async def change_pick_year(callback: CallbackQuery):
    if callback.data is None or callback.message is None:
        return
        
    _, year = callback.data.split(":")
    from app.telegram.ui.calendar import build_year_keyboard
    
    await callback.message.edit_text(
        f"📅 <b>Выберите месяц ({year})</b>",
        reply_markup=build_year_keyboard(int(year), prefix="checkin"),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    """Обработчик для неактивных кнопок (дни недели, пустые ячейки)"""
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("checkin:"))
async def select_checkin_date(callback: CallbackQuery):
    """Обработчик выбора даты заезда"""
    if callback.from_user is None or callback.message is None or callback.data is None:
        return
    
    user_id = callback.from_user.id
    _, date_str = callback.data.split(":")
    selected_date = datetime.date.fromisoformat(date_str)
    
    # Сохраняем дату заезда
    if user_id not in availability_states:
        availability_states[user_id] = AvailabilityState()
    
    availability_states[user_id].check_in = selected_date
    
    # Показываем календарь для выбора даты выезда
    await callback.message.edit_text(
        f"📅 <b>Выберите дату выезда</b>\n\n"
        f"Заезд: {selected_date.strftime('%d.%m.%Y')}",
        reply_markup=build_month_keyboard(
            selected_date.year,
            selected_date.month,
            prefix="checkout",
            min_date=selected_date + datetime.timedelta(days=1),  # Минимум на следующий день
        ),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("checkout_month:"))
async def change_checkout_month(callback: CallbackQuery):
    """Переключение месяца при выборе даты выезда"""
    if callback.data is None or callback.message is None or callback.from_user is None:
        return

    user_id = callback.from_user.id
    state = availability_states.get(user_id)
    
    if not state or not state.check_in:
        await callback.answer("Сначала выберите дату заезда")
        return

    _, value = callback.data.split(":")
    year, month = map(int, value.split("-"))

    await callback.message.edit_text(
        f"📅 <b>Выберите дату выезда</b>\n\n"
        f"Заезд: {state.check_in.strftime('%d.%m.%Y')}",
        reply_markup=build_month_keyboard(
            year,
            month,
            prefix="checkout",
            min_date=state.check_in + datetime.timedelta(days=1),
        ),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("checkout:"))
async def select_checkout_date(callback: CallbackQuery):
    """Обработчик выбора даты выезда"""
    if callback.from_user is None or callback.message is None or callback.data is None:
        return
    
    user_id = callback.from_user.id
    state = availability_states.get(user_id)
    
    if not state or not state.check_in:
        await callback.answer("Сначала выберите дату заезда")
        return
    
    _, date_str = callback.data.split(":")
    selected_date = datetime.date.fromisoformat(date_str)
    
    # Проверка что дата выезда после заезда
    if selected_date <= state.check_in:
        await callback.answer("Дата выезда должна быть позже даты заезда", show_alert=True)
        return
    
    state.check_out = selected_date
    
    # Вычисляем количество ночей
    nights = (selected_date - state.check_in).days
    
    # Запрашиваем свободные дома
    available_houses = await booking_service.get_available_houses(state.check_in, state.check_out)

    if not available_houses:
        back_callback = "admin:menu" if is_admin(user_id) else "guest:menu"
        retry_callback = "admin:availability" if is_admin(user_id) else "guest:availability"

        await callback.message.edit_text(
            f"🚫 <b>Нет свободных домиков</b>\n\n"
            f"📅 Даты: {state.check_in.strftime('%d.%m.%Y')} - {state.check_out.strftime('%d.%m.%Y')}\n"
            f"Попробуйте выбрать другие даты.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Выбрать другие даты", callback_data=retry_callback)],
                [InlineKeyboardButton(text="🔙 В меню", callback_data=back_callback)]
            ])
        )
        await callback.answer()
        return

    # Формируем список доступных домов
    text = (
        f"✅ <b>Доступные домики:</b>\n\n"
        f"📅 {state.check_in.strftime('%d.%m.%Y')} — {state.check_out.strftime('%d.%m.%Y')}\n"
        f"🌙 Ночей: {nights}\n"
        f"──────────────────\n"
    )
    
    buttons = []
    for house in available_houses:
        text += f"🏠 <b>{house.name}</b>\n"
        if house.description:
            text += f"ℹ️ {house.description}\n"
        text += f"👥 До {house.capacity} гостей\n\n"
        
        # Кнопка бронирования
        buttons.append([
            InlineKeyboardButton(
                text=f"✅ Забронировать {house.name}", 
                callback_data=f"booking:create:{house.id}"
            )
        ])
        
    buttons.append([InlineKeyboardButton(text="🔄 Выбрать другие даты", callback_data="admin:availability" if is_admin(user_id) else "guest:availability")])
    buttons.append([InlineKeyboardButton(text="🔙 В меню", callback_data="admin:menu" if is_admin(user_id) else "guest:menu")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()
