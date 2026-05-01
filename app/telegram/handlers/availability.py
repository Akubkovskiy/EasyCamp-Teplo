import datetime
import logging

from aiogram import Router
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from app.services.booking_service import BookingService
from app.database import AsyncSessionLocal
from app.telegram.auth.admin import is_admin

from app.telegram.ui.calendar import build_month_keyboard
from app.telegram.state.availability import (
    availability_states,
    AvailabilityState,
)

router = Router()
logger = logging.getLogger(__name__)


def _back_cb(user_id: int) -> str:
    return "admin:menu" if is_admin(user_id) else "guest:showcase:menu"


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
            back_callback=_back_cb(user_id),
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
            back_callback=_back_cb(user_id),
        ),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("checkin_month:"))
async def change_checkin_month(callback: CallbackQuery):
    if callback.data is None or callback.message is None:
        return

    _, value = callback.data.split(":")
    year, month = map(int, value.split("-"))
    uid = callback.from_user.id if callback.from_user else 0

    await callback.message.edit_text(
        "📅 <b>Выберите дату заезда</b>",
        reply_markup=build_month_keyboard(
            year,
            month,
            prefix="checkin",
            back_callback=_back_cb(uid),
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
            min_date=selected_date
            + datetime.timedelta(days=1),  # Минимум на следующий день
            back_callback=_back_cb(user_id),
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

    uid = callback.from_user.id if callback.from_user else 0
    await callback.message.edit_text(
        f"📅 <b>Выберите дату выезда</b>\n\n"
        f"Заезд: {state.check_in.strftime('%d.%m.%Y')}",
        reply_markup=build_month_keyboard(
            year,
            month,
            prefix="checkout",
            min_date=state.check_in + datetime.timedelta(days=1),
            back_callback=_back_cb(uid),
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
        await callback.answer(
            "Дата выезда должна быть позже даты заезда", show_alert=True
        )
        return

    state.check_out = selected_date

    # Вычисляем количество ночей
    nights = (selected_date - state.check_in).days

    # Запрашиваем свободные дома
    async with AsyncSessionLocal() as db:
        available_houses = await BookingService.get_available_houses(
            db, state.check_in, state.check_out
        )

    if not available_houses:
        back_callback = "admin:menu" if is_admin(user_id) else "guest:showcase:menu"
        retry_callback = (
            "admin:availability" if is_admin(user_id) else "guest:availability"
        )

        await callback.message.edit_text(
            f"🚫 <b>Нет свободных домиков</b>\n\n"
            f"📅 Даты: {state.check_in.strftime('%d.%m.%Y')} - {state.check_out.strftime('%d.%m.%Y')}\n"
            f"Попробуйте выбрать другие даты.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔄 Выбрать другие даты", callback_data=retry_callback
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 В меню", callback_data=back_callback
                        )
                    ],
                ]
            ),
        )
        await callback.answer()
        return

    # Формируем карточки доступных домов с фото и ценами
    from app.services.pricing_service import PricingService
    from app.data.house_descriptions import get_display_description

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    date_from = state.check_in.strftime("%d.%m.%Y")
    date_to = state.check_out.strftime("%d.%m.%Y")
    header = (
        f"🏕 <b>Свободные домики</b>\n"
        f"📅 {date_from} — {date_to} · {nights} {'ночь' if nights == 1 else 'ночи' if 2 <= nights <= 4 else 'ночей'}"
    )
    await callback.message.answer(header, parse_mode="HTML")

    async with AsyncSessionLocal() as db:
        for house in available_houses:
            desc = get_display_description(house.name, house.description)

            stay = await PricingService.calculate_stay_total(
                db, house.id, state.check_in, state.check_out
            )
            total = stay["total"]
            avg = stay["avg_per_night"]
            total_orig = stay.get("total_without_discount", total)

            # Карточка: название + вместимость
            card = f"🏠 <b>{house.name}</b>  ·  до {house.capacity} гостей\n"
            if desc:
                card += f"\n{desc}\n"

            # Цена
            if total > 0:
                card += "\n"
                if total < total_orig:
                    card += (
                        f"💰 <b>{total:,} ₽</b>  <s>{total_orig:,} ₽</s>\n"
                        f"<i>{avg:,} ₽/ночь × {nights}</i>\n"
                    )
                else:
                    card += (
                        f"💰 <b>{total:,} ₽</b>\n"
                        f"<i>{avg:,} ₽/ночь × {nights}</i>\n"
                    )
            elif house.base_price > 0:
                card += f"\n💰 от <b>{house.base_price:,} ₽/ночь</b>\n"

            btn_text = "✅ Забронировать"
            if total > 0:
                btn_text += f" — {total:,} ₽"
            book_callback = (
                f"booking:create:{house.id}"
                if is_admin(user_id)
                else f"guest:book:{house.id}"
            )
            house_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn_text, callback_data=book_callback)]
            ])

            if house.promo_image_id:
                await callback.message.answer_photo(
                    photo=house.promo_image_id,
                    caption=card,
                    reply_markup=house_kb,
                    parse_mode="HTML",
                )
            else:
                await callback.message.answer(card, reply_markup=house_kb, parse_mode="HTML")

    nav_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔄 Другие даты",
            callback_data="admin:availability" if is_admin(user_id) else "guest:availability",
        )],
        [InlineKeyboardButton(
            text="🔙 В меню",
            callback_data="admin:menu" if is_admin(user_id) else "guest:showcase:menu",
        )],
    ])
    await callback.message.answer("─" * 20, reply_markup=nav_kb)
    await callback.answer()
