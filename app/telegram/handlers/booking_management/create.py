"""
Обработчики для СОЗДАНИЯ бронирований
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, date

from app.telegram.states.booking import BookingStates
from app.services.booking_service import booking_service
from app.services.house_service import house_service
from app.utils.validators import validate_phone, format_phone
from app.telegram.ui.calendar import build_month_keyboard, build_year_keyboard
from app.core.config import settings
from app.telegram.state.availability import availability_states

router = Router()


# Bridge handler: connects availability check to FSM booking flow
@router.callback_query(F.data.startswith("booking:create:"))
async def start_booking_from_availability(callback: CallbackQuery, state: FSMContext):
    """Начало бронирования из проверки доступности"""
    if callback.from_user is None or callback.message is None:
        return

    user_id = callback.from_user.id
    house_id = int(callback.data.split(":")[2])

    # Получаем данные из availability_states
    avail_state = availability_states.get(user_id)
    if not avail_state or not avail_state.check_in or not avail_state.check_out:
        await callback.answer(
            "❌ Ошибка: даты не найдены. Попробуйте снова.", show_alert=True
        )
        return

    # Получаем информацию о доме
    house = await house_service.get_house(house_id)
    if not house:
        await callback.answer("❌ Домик не найден", show_alert=True)
        return

    # Переносим данные в FSM
    await state.clear()
    await state.update_data(
        house_id=house_id,
        check_in=avail_state.check_in,
        check_out=avail_state.check_out,
    )

    # Вычисляем количество ночей
    nights = (avail_state.check_out - avail_state.check_in).days

    # Определяем callback для возврата
    from app.telegram.auth.admin import is_admin

    back_callback = "admin:availability" if is_admin(user_id) else "guest:availability"

    # Создаем клавиатуру с кнопками навигации
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад к выбору домика", callback_data=back_callback
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить бронирование", callback_data="cancel_booking"
                )
            ],
        ]
    )

    # Запрашиваем имя гостя
    await callback.message.edit_text(
        f"📝 <b>Бронирование {house.name}</b>\n\n"
        f"📅 Даты: {avail_state.check_in.strftime('%d.%m.%Y')} - {avail_state.check_out.strftime('%d.%m.%Y')}\n"
        f"🌙 Ночей: {nights}\n\n"
        f"Пожалуйста, введите <b>имя гостя</b>:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(BookingStates.waiting_for_guest_name)
    await callback.answer()


@router.message(Command("new_booking"))
@router.callback_query(F.data == "admin:new_booking")
async def start_new_booking(event: Message | CallbackQuery, state: FSMContext):
    """Начало создания новой брони"""
    await state.clear()

    # Получаем список домов динамически
    houses = await house_service.get_all_houses()

    keyboard_buttons = []
    for h in houses:
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🏠 {h.name}", callback_data=f"new_booking:house:{h.id}"
                )
            ]
        )
    
    keyboard_buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    text = "🆕 <b>Создание новой брони</b>\n\nВыберите домик:"

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
    
    # Fetch house name for display
    house = await house_service.get_house(house_id)
    house_name = house.name if house else f"Дом {house_id}"

    today = datetime.now().date()

    await callback.message.edit_text(
        f"🏠 Выбран домик: <b>{house_name}</b>\n\n📅 <b>Выберите дату заезда:</b>",
        reply_markup=build_month_keyboard(
            today.year, today.month, prefix="bookin", min_date=today
        ),
        parse_mode="HTML",
    )
    await state.set_state(BookingStates.waiting_for_check_in)
    await callback.answer()


# --- Календарь заезда ---


@router.callback_query(F.data.startswith("bookin_month:"))
async def change_bookin_month(callback: CallbackQuery):
    _, value = callback.data.split(":")
    year, month = map(int, value.split("-"))
    await callback.message.edit_reply_markup(
        reply_markup=build_month_keyboard(
            year, month, prefix="bookin", min_date=datetime.now().date()
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bookin_pick_month:"))
@router.callback_query(F.data.startswith("bookin_pick_year:"))
async def pick_bookin_month_year(callback: CallbackQuery):
    year = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(
        reply_markup=build_year_keyboard(year, prefix="bookin")
    )
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
            min_date.year, min_date.month, prefix="bookout", min_date=min_date
        ),
        parse_mode="HTML",
    )
    await state.set_state(BookingStates.waiting_for_check_out)
    await callback.answer()


# --- Календарь выезда ---


@router.callback_query(F.data.startswith("bookout_month:"))
async def change_bookout_month(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    check_in = data.get("check_in")
    _, value = callback.data.split(":")
    year, month = map(int, value.split("-"))
    await callback.message.edit_reply_markup(
        reply_markup=build_month_keyboard(
            year,
            month,
            prefix="bookout",
            min_date=(check_in + timedelta(days=1)) if check_in else None,
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bookout_pick_month:"))
@router.callback_query(F.data.startswith("bookout_pick_year:"))
async def pick_bookout_month_year(callback: CallbackQuery):
    year = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(
        reply_markup=build_year_keyboard(year, prefix="bookout")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bookout:"))
async def select_checkout_date(callback: CallbackQuery, state: FSMContext):
    """Дата выезда выбрана -> Проверка и ввод имени"""
    date_str = callback.data.split(":")[1]
    check_out = datetime.fromisoformat(date_str).date()
    data = await state.get_data()
    check_in = data.get("check_in")

    is_available = await booking_service.check_availability(
        data["house_id"], check_in, check_out
    )

    if not is_available:
        # UX FIX: Добавляем кнопку возврата к заезду
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Выбрать заезд заново",
                        callback_data=f"new_booking:house:{data['house_id']}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена", callback_data="cancel_booking"
                    )
                ],
            ]
        )
        await callback.message.edit_text(
            f"❌ <b>Даты {check_in.strftime('%d.%m')} - {check_out.strftime('%d.%m')} ЗАНЯТЫ!</b>\n\n"
            f"Попробуйте выбрать другой период для домика {data['house_id']}.",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        await callback.answer("Даты заняты", show_alert=True)
        return

    await state.update_data(check_out=check_out)

    nights = (check_out - check_in).days

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад к выбору дат", callback_data="back_to_checkout"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить бронирование", callback_data="cancel_booking"
                )
            ],
        ]
    )

    await callback.message.edit_text(
        f"📅 <b>Период: {check_in.strftime('%d.%m.%Y')} - {check_out.strftime('%d.%m.%Y')} ({nights} сут.)</b>\n\n"
        "👤 <b>Введите имя гостя:</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(BookingStates.waiting_for_guest_name)
    await callback.answer()


# --- Данные гостя ---


@router.message(BookingStates.waiting_for_guest_name)
async def guest_name_entered(message: Message, state: FSMContext):
    await state.update_data(guest_name=message.text)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад к выбору дат", callback_data="back_to_checkout"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить бронирование", callback_data="cancel_booking"
                )
            ],
        ]
    )

    await message.answer(
        "📞 Введите телефон гостя (например: +79991234567):", reply_markup=keyboard
    )
    await state.set_state(BookingStates.waiting_for_guest_phone)


@router.message(BookingStates.waiting_for_guest_phone)
async def guest_phone_entered(message: Message, state: FSMContext):
    phone = message.text
    if not validate_phone(phone):
        await message.answer("❌ Некорректный номер телефона. Попробуйте еще раз.")
        return
    await state.update_data(guest_phone=format_phone(phone))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад к имени", callback_data="back_to_name"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить бронирование", callback_data="cancel_booking"
                )
            ],
        ]
    )

    await message.answer("👥 Введите количество гостей (число):", reply_markup=keyboard)
    await state.set_state(BookingStates.waiting_for_guests_count)


@router.message(BookingStates.waiting_for_guests_count)
async def guests_count_entered(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return
    count = int(message.text)

    data = await state.get_data()
    house_id = data["house_id"]

    # Проверка вместимости
    house = await house_service.get_house(house_id)
    if house and count > house.capacity:
        await message.answer(
            f"❌ <b>Слишком много гостей!</b>\n"
            f"Домик {house.name} вмещает максимум {house.capacity} чел.\n\n"
            "Пожалуйста, введите корректное количество:",
            parse_mode="HTML",
        )
        return

    await state.update_data(guests_count=count)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад к телефону", callback_data="back_to_phone"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")],
        ]
    )

    await message.answer(
        "💰 <b>Введите сумму предоплаты (RUB):</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(BookingStates.waiting_for_prepayment)


# --- Финализация ---


@router.message(BookingStates.waiting_for_prepayment)
async def prepayment_entered(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return
    prepayment = int(message.text)
    await state.update_data(advance_amount=prepayment)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад к предоплате", callback_data="back_to_prepayment"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")],
        ]
    )

    await message.answer(
        "💰 <b>Введите остаток при заселении (RUB):</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(BookingStates.waiting_for_remainder)


@router.message(BookingStates.waiting_for_remainder)
async def remainder_entered(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return
    remainder = int(message.text)
    await state.update_data(remainder_amount=remainder)

    # Calculate total price
    data = await state.get_data()
    total_price = data["advance_amount"] + remainder
    await state.update_data(total_price=total_price)

    # Status selection
    buttons = [
        [InlineKeyboardButton(text="⏳ Ожидает оплаты", callback_data="status:new")],
        [
            InlineKeyboardButton(
                text="✅ Ждёт заселения (Оплачено)", callback_data="status:confirmed"
            )
        ],
    ]

    # Если заезд сегодня, добавляем статус "Заезд сегодня"
    if data["check_in"] == date.today():
        buttons.insert(
            0,
            [
                InlineKeyboardButton(
                    text="🔔 Заезд сегодня", callback_data="status:checking_in"
                )
            ],
        )

    buttons.extend(
        [
            [
                InlineKeyboardButton(
                    text="🔙 Назад к остатку", callback_data="back_to_remainder"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")],
        ]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        "📊 <b>Выберите статус бронирования:</b>\n"
        f"Общая цена: {total_price}₽ (Предоплата: {data['advance_amount']}₽, Остаток: {remainder}₽)",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(BookingStates.waiting_for_status)


@router.callback_query(BookingStates.waiting_for_status, F.data.startswith("status:"))
async def status_selected(callback: CallbackQuery, state: FSMContext):
    status_val = callback.data.split(":")[1]
    await state.update_data(status=status_val)

    data = await state.get_data()
    nights = (data["check_out"] - data["check_in"]).days

    # Map status to readable
    status_map = {
        "new": "⏳ Ожидает оплаты",
        "confirmed": "✅ Ждёт заселения",
        "checking_in": "🔔 Заезд сегодня",
    }
    status_text = status_map.get(status_val, status_val)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить и создать", callback_data="confirm_booking"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад к статусу", callback_data="back_to_status"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")],
        ]
    )

    # Fetch house name again if possible or just use ID (to be safe/fast)
    # Ideally should store name in state, but simpler to just show ID or "Дом ID"
    # Actually, let's fetch it for better UX
    house = await house_service.get_house(data['house_id'])
    house_name = house.name if house else f"Дом {data['house_id']}"

    await callback.message.edit_text(
        "📋 <b>Подтверждение бронирования</b>\n\n"
        f"🏠 Домик: <b>{house_name}</b>\n"
        f"📅 Даты: {data['check_in'].strftime('%d.%m.%Y')} - {data['check_out'].strftime('%d.%m.%Y')} ({nights} н.)\n"
        f"👤 Гость: {data['guest_name']} ({data['guest_phone']})\n"
        f"👥 Гостей: {data['guests_count']}\n\n"
        f"💰 <b>Цена: {data['total_price']}₽</b>\n"
        f"💵 Предоплата: {data['advance_amount']}₽\n"
        f"🪙 Остаток: {data['remainder_amount']}₽\n"
        f"📊 Статус: {status_text}",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
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
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🏕 Главное меню", callback_data="admin:menu"
                        )
                    ]
                ]
            ),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text("❌ Ошибка при создании брони.")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_booking")
async def cancel_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="admin:menu")]
        ]
    )

    await callback.message.edit_text(
        "❌ Создание брони отменено.", reply_markup=keyboard
    )
    await callback.answer()


# --- Back Navigation Handlers ---


@router.callback_query(F.data == "back_to_checkout")
async def back_to_checkout_selection(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору даты выезда"""
    data = await state.get_data()
    check_in = data.get("check_in")

    if not check_in:
        await callback.answer("❌ Ошибка: дата заезда не найдена", show_alert=True)
        return

    min_date = check_in + timedelta(days=1)

    await callback.message.edit_text(
        f"📅 <b>Дата заезда: {check_in.strftime('%d.%m.%Y')}</b>\n\n"
        "📅 <b>Выберите дату выезда:</b>",
        reply_markup=build_month_keyboard(
            min_date.year, min_date.month, prefix="bookout", min_date=min_date
        ),
        parse_mode="HTML",
    )
    await state.set_state(BookingStates.waiting_for_check_out)
    await callback.answer()


@router.callback_query(F.data == "back_to_name")
async def back_to_name_input(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу имени гостя"""
    data = await state.get_data()
    check_in = data.get("check_in")
    check_out = data.get("check_out")

    if not check_in or not check_out:
        await callback.answer("❌ Ошибка: даты не найдены", show_alert=True)
        return

    nights = (check_out - check_in).days

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад к выбору дат", callback_data="back_to_checkout"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить бронирование", callback_data="cancel_booking"
                )
            ],
        ]
    )

    await callback.message.edit_text(
        f"📅 <b>Период: {check_in.strftime('%d.%m.%Y')} - {check_out.strftime('%d.%m.%Y')} ({nights} сут.)</b>\n\n"
        "👤 <b>Введите имя гостя:</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(BookingStates.waiting_for_guest_name)
    await callback.answer()


@router.callback_query(F.data == "back_to_phone")
async def back_to_phone_input(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу телефона"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад к имени", callback_data="back_to_name"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить бронирование", callback_data="cancel_booking"
                )
            ],
        ]
    )

    await callback.message.edit_text(
        "📞 Введите телефон гостя (например: +79991234567):", reply_markup=keyboard
    )
    await state.set_state(BookingStates.waiting_for_guest_phone)
    await callback.answer()


@router.callback_query(F.data == "back_to_guests_count")
async def back_to_guests_count_input(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу количества гостей"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад к телефону", callback_data="back_to_phone"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить бронирование", callback_data="cancel_booking"
                )
            ],
        ]
    )

    await callback.message.edit_text(
        "👥 Введите количество гостей (число):", reply_markup=keyboard
    )
    await state.set_state(BookingStates.waiting_for_guests_count)
    await callback.answer()


@router.callback_query(F.data == "back_to_confirmation")
async def back_to_confirmation_screen(callback: CallbackQuery, state: FSMContext):
    """Возврат к экрану подтверждения"""
    data = await state.get_data()

    # Проверяем наличие всех необходимых данных
    required_fields = [
        "house_id",
        "check_in",
        "check_out",
        "guest_name",
        "guest_phone",
        "guests_count",
        "total_price",
    ]
    if not all(field in data for field in required_fields):
        await callback.answer(
            "❌ Ошибка: данные бронирования неполные", show_alert=True
        )
        return

    nights = (data["check_out"] - data["check_in"]).days
    price = data["total_price"]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Подтвердить: {price}₽", callback_data="confirm_booking"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить цену", callback_data="change_price"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад к количеству гостей",
                    callback_data="back_to_guests_count",
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")],
        ]
    )

    house = await house_service.get_house(data['house_id'])
    house_name = house.name if house else f"Дом {data['house_id']}"

    await callback.message.edit_text(
        "📋 <b>Подтверждение бронирования</b>\n\n"
        f"🏠 Домик: <b>{house_name}</b>\n"
        f"📅 Даты: {data['check_in'].strftime('%d.%m.%Y')} - {data['check_out'].strftime('%d.%m.%Y')} ({nights} н.)\n"
        f"👤 Гость: {data['guest_name']} ({data['guest_phone']})\n"
        f"👥 Гостей: {data['guests_count']}\n"
        f"💰 <b>Цена: {price}₽</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(BookingStates.waiting_for_confirmation)
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_calendar_click(callback: CallbackQuery):
    await callback.answer()
