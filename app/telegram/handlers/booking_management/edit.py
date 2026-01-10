"""
Обработчики для РЕДАКТИРОВАНИЯ бронирований
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from app.telegram.states.booking import BookingStates
from app.services.booking_service import booking_service
from app.models import BookingStatus
from app.utils.validators import validate_phone, format_phone
from app.telegram.ui.calendar import build_month_keyboard, build_year_keyboard

router = Router()

@router.callback_query(F.data.startswith("booking:edit:"))
async def show_edit_menu(callback: CallbackQuery):
    """Меню выбора поля для редактирования"""
    booking_id = int(callback.data.split(":")[2])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Даты", callback_data=f"booking:edit_f:{booking_id}:dates")],
        [InlineKeyboardButton(text="👤 Имя гостя", callback_data=f"booking:edit_f:{booking_id}:name")],
        [InlineKeyboardButton(text="📞 Телефон", callback_data=f"booking:edit_f:{booking_id}:phone")],
        [InlineKeyboardButton(text="👥 Кол-во гостей", callback_data=f"booking:edit_f:{booking_id}:count")],
        [InlineKeyboardButton(text="💰 Цена", callback_data=f"booking:edit_f:{booking_id}:price")],
        [InlineKeyboardButton(text="📊 Статус", callback_data=f"booking:edit_f:{booking_id}:status")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"booking:view:{booking_id}")]
    ])
    
    await callback.message.edit_text(
        f"✏️ <b>Редактирование брони #{booking_id}</b>\n\nВыберите, что хотите изменить:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("booking:edit_f:"))
async def start_editing_field(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования конкретного поля"""
    parts = callback.data.split(":")
    booking_id = int(parts[2])
    field = parts[3]
    await state.clear() # На всякий случай
    await state.update_data(editing_booking_id=booking_id)
    
    if field == "dates":
        today = datetime.now().date()
        await callback.message.edit_text(
            f"✏️ <b>Новые даты для брони #{booking_id}</b>\n\n"
            "📅 <b>Выберите новую дату заезда:</b>",
            reply_markup=build_month_keyboard(today.year, today.month, prefix="ebin", min_date=today),
            parse_mode="HTML"
        )
        await state.set_state(BookingStates.editing_dates)
    elif field == "name":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к брони", callback_data=f"booking:cancel_edit:{booking_id}")]
        ])
        await callback.message.edit_text("👤 Введите новое имя гостя:", reply_markup=keyboard)
        await state.set_state(BookingStates.editing_guest_name)
    elif field == "phone":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к брони", callback_data=f"booking:cancel_edit:{booking_id}")]
        ])
        await callback.message.edit_text("📞 Введите новый номер телефона:", reply_markup=keyboard)
        await state.set_state(BookingStates.editing_guest_phone)
    elif field == "count":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к брони", callback_data=f"booking:cancel_edit:{booking_id}")]
        ])
        await callback.message.edit_text("👥 Введите количество гостей:", reply_markup=keyboard)
        await state.set_state(BookingStates.editing_guests_count)
    elif field == "price":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к брони", callback_data=f"booking:cancel_edit:{booking_id}")]
        ])
        await callback.message.edit_text("💰 Введите новую стоимость (руб):", reply_markup=keyboard)
        await state.set_state(BookingStates.editing_price)
    elif field == "status":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆕 NEW", callback_data=f"booking:st:{booking_id}:new")],
            [InlineKeyboardButton(text="✅ CONFIRMED", callback_data=f"booking:st:{booking_id}:confirmed")],
            [InlineKeyboardButton(text="💰 PAID", callback_data=f"booking:st:{booking_id}:paid")],
            [InlineKeyboardButton(text="🏁 COMPLETED", callback_data=f"booking:st:{booking_id}:completed")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"booking:edit:{booking_id}")]
        ])
        await callback.message.edit_text("📊 Выберите новый статус:", reply_markup=keyboard)
    
    await callback.answer()

# --- Календарь редактирования ---

@router.callback_query(F.data.startswith("ebin_month:"))
async def change_ebin_month(callback: CallbackQuery):
    _, value = callback.data.split(":")
    year, month = map(int, value.split("-"))
    await callback.message.edit_reply_markup(
        reply_markup=build_month_keyboard(year, month, prefix="ebin", min_date=datetime.now().date())
    )
    await callback.answer()

@router.callback_query(F.data.startswith("ebin:"))
async def select_edit_checkin_date(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split(":")[1]
    check_in = datetime.fromisoformat(date_str).date()
    await state.update_data(new_check_in=check_in)
    
    min_date = check_in + timedelta(days=1)
    
    await callback.message.edit_text(
        f"📅 <b>Новая дата заезда: {check_in.strftime('%d.%m.%Y')}</b>\n\n"
        "📅 <b>Выберите новую дату выезда:</b>",
        reply_markup=build_month_keyboard(
            min_date.year, min_date.month, prefix="ebout",
            min_date=min_date
        ),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("ebout_month:"))
async def change_ebout_month(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    check_in = data.get('new_check_in')
    _, value = callback.data.split(":")
    year, month = map(int, value.split("-"))
    await callback.message.edit_reply_markup(
        reply_markup=build_month_keyboard(
            year, month, prefix="ebout", 
            min_date=(check_in + timedelta(days=1)) if check_in else None
        )
    )
    await callback.answer()

@router.callback_query(F.data.startswith("ebout:"))
async def select_edit_checkout_date(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split(":")[1]
    check_out = datetime.fromisoformat(date_str).date()
    data = await state.get_data()
    check_in = data.get('new_check_in')
    booking_id = data.get('editing_booking_id')
    
    booking = await booking_service.get_booking(booking_id)
    is_available = await booking_service.check_availability(
        booking.house_id, check_in, check_out, exclude_booking_id=booking_id
    )
    
    if not is_available:
        # UX FIX: Добавляем кнопку возврата к заезду
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Выбрать заезд заново", callback_data=f"booking:edit_f:{booking_id}:dates")],
            [InlineKeyboardButton(text="🔙 В меню редактирования", callback_data=f"booking:edit:{booking_id}")]
        ])
        await callback.message.edit_text(
            f"❌ <b>Даты {check_in.strftime('%d.%m')} - {check_out.strftime('%d.%m')} ЗАНЯТЫ!</b>\n\n"
            f"Попробуйте выбрать другой период.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer("Даты заняты", show_alert=True)
        return

    success = await booking_service.update_booking(booking_id, check_in=check_in, check_out=check_out)
    if success:
        await callback.message.answer(f"✅ Даты в брони #{booking_id} обновлены.")
    else:
        await callback.message.answer("❌ Ошибка при обновлении.")
    
    await state.clear()
    await send_booking_details_refreshed(callback.message, booking_id)
    await callback.answer()

# --- Обработка статуса ---

@router.callback_query(F.data.startswith("booking:st:"))
async def process_edit_status(callback: CallbackQuery):
    parts = callback.data.split(":")
    booking_id = int(parts[2])
    status_map = {
        "new": BookingStatus.NEW,
        "confirmed": BookingStatus.CONFIRMED,
        "paid": BookingStatus.PAID,
        "completed": BookingStatus.COMPLETED
    }
    await booking_service.update_booking(booking_id, status=status_map[parts[3]])
    await callback.answer("✅ Статус обновлен")
    await send_booking_details_refreshed(callback.message, booking_id, edit_instead=True)

# --- Обработка текстовых полей ---

@router.callback_query(F.data.startswith("booking:cancel_edit:"))
async def cancel_edit_booking(callback: CallbackQuery, state: FSMContext):
    """Отмена редактирования и возврат к просмотру брони"""
    booking_id = int(callback.data.split(":")[2])
    await state.clear()
    await callback.answer("Редактирование отменено")
    await send_booking_details_refreshed(callback.message, booking_id, edit_instead=True)

@router.message(BookingStates.editing_guest_name)
async def process_edit_name(message: Message, state: FSMContext):
    data = await state.get_data()
    bid = data['editing_booking_id']
    await booking_service.update_booking(bid, guest_name=message.text)
    await message.answer(f"✅ Имя в брони #{bid} обновлено.")
    await state.clear()
    await send_booking_details_refreshed(message, bid)

@router.message(BookingStates.editing_guest_phone)
async def process_edit_phone(message: Message, state: FSMContext):
    if not validate_phone(message.text):
        await message.answer("❌ Неверный формат.")
        return
    data = await state.get_data()
    bid = data['editing_booking_id']
    await booking_service.update_booking(bid, guest_phone=format_phone(message.text))
    await message.answer(f"✅ Телефон в брони #{bid} обновлен.")
    await state.clear()
    await send_booking_details_refreshed(message, bid)

@router.message(BookingStates.editing_guests_count)
async def process_edit_count(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return
    data = await state.get_data()
    bid = data['editing_booking_id']
    await booking_service.update_booking(bid, guests_count=int(message.text))
    await message.answer(f"✅ Количество гостей в брони #{bid} обновлено.")
    await state.clear()
    await send_booking_details_refreshed(message, bid)

@router.message(BookingStates.editing_price)
async def process_edit_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        data = await state.get_data()
        bid = data['editing_booking_id']
        await booking_service.update_booking(bid, total_price=price)
        await message.answer(f"✅ Цена в брони #{bid} обновлена.")
        await state.clear()
        await send_booking_details_refreshed(message, bid)
    except ValueError:
        await message.answer("❌ Введите число.")

# --- Вспомогательные функции ---

# --- Вспомогательные функции ---

async def send_booking_details_refreshed(message_or_event, booking_id, edit_instead=False):
    from .view import render_booking_card
    # Просто передаем событие (Message или CallbackQuery) в рендерер
    # Он сам разберется: если Message - отправит новое, если Callback - отредактирует
    await render_booking_card(message_or_event, booking_id)
