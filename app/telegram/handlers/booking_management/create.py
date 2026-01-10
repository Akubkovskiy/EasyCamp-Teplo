"""
Обработчики для СОЗДАНИЯ бронирований
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from app.telegram.states.booking import BookingStates
from app.services.booking_service import booking_service
from app.services.house_service import house_service
from app.utils.validators import validate_phone, format_phone
from app.telegram.ui.calendar import build_month_keyboard, build_year_keyboard
from app.core.config import settings

router = Router()

@router.message(Command("new_booking"))
@router.callback_query(F.data == "admin:new_booking")
async def start_new_booking(event: Message | CallbackQuery, state: FSMContext):
    """Начало создания новой брони"""
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Teplo 1", callback_data="new_booking:house:1")],
        [InlineKeyboardButton(text="🏠 Teplo 2", callback_data="new_booking:house:2")],
        [InlineKeyboardButton(text="🏠 Teplo 3", callback_data="new_booking:house:3")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")]
    ])
    
    text = (
        "🆕 <b>Создание новой брони</b>\n\n"
        "Выберите домик:"
    )
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
    await state.set_state(BookingStates.waiting_for_house)

@router.callback_query(F.data.startswith("new_booking:house:"))
async def house_selected(callback: CallbackQuery, state: FSMContext):
    """Домик выбран -> Календарь заезда"""
    house_id = int(callback.data.split(":")[2])
    await state.update_data(house_id=house_id)
    
    today = datetime.now().date()
    
    await callback.message.edit_text(
        f"🏠 Выбран домик: <b>Teplo {house_id}</b>\n\n"
        "📅 <b>Выберите дату заезда:</b>",
        reply_markup=build_month_keyboard(today.year, today.month, prefix="bookin", min_date=today),
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.waiting_for_check_in)
    await callback.answer()

# --- Календарь заезда ---

@router.callback_query(F.data.startswith("bookin_month:"))
async def change_bookin_month(callback: CallbackQuery):
    _, value = callback.data.split(":")
    year, month = map(int, value.split("-"))
    await callback.message.edit_reply_markup(
        reply_markup=build_month_keyboard(year, month, prefix="bookin", min_date=datetime.now().date())
    )
    await callback.answer()

@router.callback_query(F.data.startswith("bookin_pick_month:"))
@router.callback_query(F.data.startswith("bookin_pick_year:"))
async def pick_bookin_month_year(callback: CallbackQuery):
    year = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(reply_markup=build_year_keyboard(year, prefix="bookin"))
    await callback.answer()

@router.callback_query(F.data.startswith("bookin:"))
async def select_checkin_date(callback: CallbackQuery, state: FSMContext):
    """Дата заезда выбрана -> Календарь выезда"""
    date_str = callback.data.split(":")[1]
    check_in = datetime.fromisoformat(date_str).date()
    await state.update_data(check_in=check_in)
    
    min_date = check_in + timedelta(days=1)
    
    await callback.message.edit_text(
        f"📅 <b>Дата заезда: {check_in.strftime('%d.%m.%Y')}</b>\n\n"
        "📅 <b>Выберите дату выезда:</b>",
        reply_markup=build_month_keyboard(
            min_date.year, min_date.month, prefix="bookout",
            min_date=min_date
        ),
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.waiting_for_check_out)
    await callback.answer()

# --- Календарь выезда ---

@router.callback_query(F.data.startswith("bookout_month:"))
async def change_bookout_month(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    check_in = data.get('check_in')
    _, value = callback.data.split(":")
    year, month = map(int, value.split("-"))
    await callback.message.edit_reply_markup(
        reply_markup=build_month_keyboard(
            year, month, prefix="bookout", 
            min_date=(check_in + timedelta(days=1)) if check_in else None
        )
    )
    await callback.answer()

@router.callback_query(F.data.startswith("bookout_pick_month:"))
@router.callback_query(F.data.startswith("bookout_pick_year:"))
async def pick_bookout_month_year(callback: CallbackQuery):
    year = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(reply_markup=build_year_keyboard(year, prefix="bookout"))
    await callback.answer()

@router.callback_query(F.data.startswith("bookout:"))
async def select_checkout_date(callback: CallbackQuery, state: FSMContext):
    """Дата выезда выбрана -> Проверка и ввод имени"""
    date_str = callback.data.split(":")[1]
    check_out = datetime.fromisoformat(date_str).date()
    data = await state.get_data()
    check_in = data.get('check_in')
    
    is_available = await booking_service.check_availability(data['house_id'], check_in, check_out)
    
    if not is_available:
        # UX FIX: Добавляем кнопку возврата к заезду
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Выбрать заезд заново", callback_data=f"new_booking:house:{data['house_id']}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")]
        ])
        await callback.message.edit_text(
            f"❌ <b>Даты {check_in.strftime('%d.%m')} - {check_out.strftime('%d.%m')} ЗАНЯТЫ!</b>\n\n"
            f"Попробуйте выбрать другой период для домика Teplo {data['house_id']}.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer("Даты заняты", show_alert=True)
        return

    await state.update_data(check_out=check_out)
    
    nights = (check_out - check_in).days
    
    await callback.message.edit_text(
        f"📅 <b>Период: {check_in.strftime('%d.%m.%Y')} - {check_out.strftime('%d.%m.%Y')} ({nights} сут.)</b>\n\n"
        "👤 <b>Введите имя гостя:</b>",
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.waiting_for_guest_name)
    await callback.answer()

# --- Данные гостя ---

@router.message(BookingStates.waiting_for_guest_name)
async def guest_name_entered(message: Message, state: FSMContext):
    await state.update_data(guest_name=message.text)
    await message.answer("📞 Введите телефон гостя (например: +79991234567):")
    await state.set_state(BookingStates.waiting_for_guest_phone)

@router.message(BookingStates.waiting_for_guest_phone)
async def guest_phone_entered(message: Message, state: FSMContext):
    phone = message.text
    if not validate_phone(phone):
        await message.answer("❌ Некорректный номер телефона. Попробуйте еще раз.")
        return
    await state.update_data(guest_phone=format_phone(phone))
    await message.answer("👥 Введите количество гостей (число):")
    await state.set_state(BookingStates.waiting_for_guests_count)

@router.message(BookingStates.waiting_for_guests_count)
async def guests_count_entered(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return
    count = int(message.text)
    
    data = await state.get_data()
    house_id = data['house_id']
    
    # Проверка вместимости
    house = await house_service.get_house(house_id)
    if house and count > house.capacity:
        await message.answer(
            f"❌ <b>Слишком много гостей!</b>\n"
            f"Домик {house.name} вмещает максимум {house.capacity} чел.\n\n"
            "Пожалуйста, введите корректное количество:",
            parse_mode="HTML"
        )
        return
        
    await state.update_data(guests_count=count)
    
    nights = (data['check_out'] - data['check_in']).days
    price = 5000 * nights # Placeholder
    await state.update_data(total_price=price)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Подтвердить: {price}₽", callback_data="confirm_booking")],
        [InlineKeyboardButton(text="✏️ Изменить цену", callback_data="change_price")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")]
    ])
    
    await message.answer(
        "📋 <b>Подтверждение бронирования</b>\n\n"
        f"🏠 Домик: <b>Teplo {data['house_id']}</b>\n"
        f"📅 Даты: {data['check_in'].strftime('%d.%m.%Y')} - {data['check_out'].strftime('%d.%m.%Y')} ({nights} н.)\n"
        f"👤 Гость: {data['guest_name']} ({data['guest_phone']})\n"
        f"👥 Гостей: {count}\n"
        f"💰 <b>Цена: {price}₽</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.waiting_for_confirmation)

# --- Финализация ---

@router.callback_query(F.data == "change_price")
async def request_manual_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("💰 Введите итоговую стоимость бронирования (RUB):")
    await state.set_state(BookingStates.waiting_for_price)
    await callback.answer()

@router.message(BookingStates.waiting_for_price)
async def price_entered(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return
    price = int(message.text)
    await state.update_data(total_price=price)
    data = await state.get_data()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")]
    ])
    await message.answer(f"💰 Новая цена: <b>{price}₽</b>. Подтверждаете?", reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(BookingStates.waiting_for_confirmation)

@router.callback_query(F.data == "confirm_booking")
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("⏳ Сохраняем бронирование...")
    booking = await booking_service.create_booking(data)
    
    if booking:
        sheet_link = f"https://docs.google.com/spreadsheets/d/{settings.google_sheets_spreadsheet_id}"
        await callback.message.edit_text(
            f"✅ <b>Бронь #{booking.id} создана!</b>\n\n"
            f"📊 <a href='{sheet_link}'>Открыть таблицу</a>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏕 Главное меню", callback_data="admin:menu")]
            ]),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Ошибка при создании брони.")
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel_booking")
async def cancel_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="admin:menu")]
    ])
    
    await callback.message.edit_text("❌ Создание брони отменено.", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "ignore")
async def ignore_calendar_click(callback: CallbackQuery):
    await callback.answer()
