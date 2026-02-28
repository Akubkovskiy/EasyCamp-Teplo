import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus, User, GlobalSetting
from app.telegram.auth.admin import (
    add_user,
    is_guest,
    is_admin,
    get_all_users,
    UserRole,
    remove_guest_user,
)
from app.telegram.menus.guest import (
    guest_menu_keyboard,
    guest_showcase_menu_keyboard,
    request_contact_keyboard,
)
from app.core.messages import messages
from app.core.config import settings
from app.utils.phone import normalize_phone, phones_match

router = Router()
logger = logging.getLogger(__name__)

_feedback_waiting_users: dict[int, str] = {}
_pay_receipt_waiting_users: dict[int, int] = {}
_guest_auth_state: dict[int, bool] = {}
_guest_context_state: dict[int, str] = {}  # showcase | guest_cabinet

FEEDBACK_CATEGORIES = {
    "booking": "Бронирование",
    "checkin": "Заселение",
    "payment": "Оплата",
    "other": "Другое",
}


def build_showcase_section_rows(current: str) -> list[list[InlineKeyboardButton]]:
    rows: list[list[InlineKeyboardButton]] = []

    sections: list[tuple[str, str, bool]] = [
        ("about", "🏕 О базе", True),
        ("houses", "🏠 Домики и фото", settings.guest_feature_showcase_houses),
        ("availability", "📅 Проверить даты и забронировать", True),
        ("faq", "❓ Популярные вопросы", settings.guest_feature_faq),
        ("location", "📍 Где мы находимся", True),
        ("contact", "📞 Связаться с нами", True),
        ("auth", "🔐 Авторизоваться", True),
    ]

    callback_map = {
        "about": "guest:showcase:about",
        "houses": "guest:showcase:houses",
        "availability": "guest:availability",
        "faq": "guest:showcase:faq",
        "location": "guest:showcase:location",
        "contact": "guest:contact_admin",
        "auth": "guest:auth",
    }

    for key, label, enabled in sections:
        if not enabled or key == current:
            continue
        rows.append([InlineKeyboardButton(text=label, callback_data=callback_map[key])])

    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="guest:showcase:menu")])
    return rows


def is_guest_authorized(user_id: int) -> bool:
    # state-first + fallback to DB role cache
    return _guest_auth_state.get(user_id, False) or is_guest(user_id)


def set_guest_auth(user_id: int, value: bool):
    _guest_auth_state[user_id] = value


def get_guest_context(user_id: int) -> str:
    ctx = _guest_context_state.get(user_id)
    if ctx:
        return ctx
    return "guest_cabinet" if is_guest_authorized(user_id) else "showcase"


def set_guest_context(user_id: int, context: str):
    _guest_context_state[user_id] = context


async def ensure_guest_context(callback: CallbackQuery, expected: str) -> bool:
    if not callback.from_user:
        return False

    current = get_guest_context(callback.from_user.id)
    if current == expected:
        return True

    # мягкий редирект в актуальный контекст
    if current == "guest_cabinet" and is_guest_authorized(callback.from_user.id):
        await safe_edit(
            callback,
            messages.GUEST_WELCOME,
            reply_markup=guest_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        set_guest_context(callback.from_user.id, "showcase")
        await safe_edit(
            callback,
            f"🏕 <b>{settings.project_name}</b> — место для отдыха в {settings.project_location}.\n\n"
            "Выберите, что хотите посмотреть:",
            reply_markup=guest_showcase_menu_keyboard(),
            parse_mode="HTML",
        )
    await callback.answer("Обновил меню по текущему режиму")
    return False


async def ensure_guest_auth(callback: CallbackQuery) -> bool:
    if callback.from_user and is_guest_authorized(callback.from_user.id):
        set_guest_context(callback.from_user.id, "guest_cabinet")
        return True

    await safe_edit(
        callback,
        f"🏕 <b>{settings.project_name}</b> — место для отдыха в {settings.project_location}.\n\n"
        "Сначала авторизуйтесь, чтобы открыть личный кабинет.",
        reply_markup=guest_showcase_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer("Сначала авторизуйтесь")
    return False


async def get_setting_value(session, key: str, default: str = "") -> str:
    setting = await session.get(GlobalSetting, key)
    return setting.value if setting and setting.value else default


async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None, parse_mode: str | None = None):
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Уже открыт")
            return
        raise


async def show_guest_menu(message: Message):
    """Показывает меню гостя: витрина (unauth) или кабинет (auth)."""
    user_id = message.from_user.id

    if is_guest_authorized(user_id):
        set_guest_context(user_id, "guest_cabinet")
        await message.answer(
            messages.GUEST_WELCOME,
            reply_markup=guest_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        set_guest_context(user_id, "showcase")
        await message.answer(
            f"🏕 <b>{settings.project_name}</b> — место для отдыха в {settings.project_location}.\n\n"
            "Выберите, что хотите посмотреть:",
            reply_markup=guest_showcase_menu_keyboard(),
            parse_mode="HTML",
        )


@router.message(F.contact)
async def handle_contact(message: Message):
    """Обработка контакта для входа"""
    contact = message.contact

    # Проверка, что контакт принадлежит отправителю
    if contact.user_id != message.from_user.id:
        await message.answer("⚠️ Пожалуйста, отправьте СВОЙ контакт через кнопку внизу.")
        return

    # Нормализация телефона
    clean_phone = normalize_phone(contact.phone_number)

    logger.info(f"Guest login attempt: {clean_phone} (user_id={message.from_user.id})")

    # Поиск брони
    async with AsyncSessionLocal() as session:
        # Ищем активные брони, где телефон совпадает
        # Примечание: в БД телефоны могут быть записаны по-разному.
        # В идеале в БД тоже хранить чистые номера.
        # Пока используем ILIKE c % для гибкости или точное совпадение если мы уверены.
        # Попробуем найти точное или частичное совпадение.

        # Для простоты ищем where phone like %clean_phone% OR clean_phone in phone
        # Но SQLite 'LIKE' is simpler.

        # Сделаем выборку всех активных и проверим в python (безопаснее для форматов)
        query = select(Booking).where(
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PAID])
        )
        result = await session.execute(query)
        bookings = result.scalars().all()

        found_booking = None
        for booking in bookings:
            if phones_match(clean_phone, booking.guest_phone):
                found_booking = booking
                break

        if found_booking:
            # УСПЕХ!
            await add_user(
                telegram_id=message.from_user.id,
                role=UserRole.GUEST,
                name=contact.first_name or "Гость",
                phone=clean_phone,
            )
            set_guest_auth(message.from_user.id, True)
            set_guest_context(message.from_user.id, "guest_cabinet")

            await message.answer(
                messages.welcome_success(message.from_user.first_name),
                reply_markup=ReplyKeyboardRemove(),  # Убираем кнопку контакта
            )
            await show_guest_menu(message)

        else:
            # НЕ НАЙДЕНО
            set_guest_auth(message.from_user.id, False)
            set_guest_context(message.from_user.id, "showcase")
            await message.answer(
                messages.BOOKING_NOT_FOUND,
                reply_markup=ReplyKeyboardRemove(),
            )


@router.callback_query(F.data == "guest:auth")
async def guest_auth_prompt(callback: CallbackQuery):
    if not await ensure_guest_context(callback, "showcase"):
        return
    """Попросить контакт для авторизации по брони."""
    await callback.message.answer(
        messages.GUEST_LOGIN_PROMPT,
        reply_markup=request_contact_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "guest:showcase:about")
async def guest_showcase_about(callback: CallbackQuery):
    if not await ensure_guest_context(callback, "showcase"):
        return
    async with AsyncSessionLocal() as session:
        about_text = await get_setting_value(
            session,
            "guest_showcase_about",
            f"🏕 <b>{settings.project_name}</b>\n\n"
            f"Мы находимся в {settings.project_location}. Уютные домики, природа и спокойный отдых.\n"
            "Выберите следующий раздел, чтобы посмотреть домики, даты и условия.",
        )
    keyboard = InlineKeyboardMarkup(inline_keyboard=build_showcase_section_rows("about"))
    await safe_edit(callback, about_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:showcase:houses")
async def guest_showcase_houses(callback: CallbackQuery):
    if not await ensure_guest_context(callback, "showcase"):
        return
    text = (
        "🏠 <b>Домики и фото</b>\n\n"
        "Раздел в доработке: скоро здесь будет галерея по каждому домику с фото и описанием.\n"
        "Пока можно проверить даты и перейти к бронированию."
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=build_showcase_section_rows("houses"))
    await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:showcase:faq")
async def guest_showcase_faq(callback: CallbackQuery):
    if not await ensure_guest_context(callback, "showcase"):
        return
    if not settings.guest_feature_faq:
        await callback.answer("Раздел FAQ временно недоступен", show_alert=True)
        return
    async with AsyncSessionLocal() as session:
        text = await get_setting_value(
            session,
            "guest_showcase_faq",
            "❓ <b>Популярные вопросы</b>\n\n"
            "• Как забронировать? — Нажмите «Проверить даты и забронировать».\n"
            "• Когда заезд/выезд? — Обычно заезд после 14:00, выезд до 12:00.\n"
            "• Можно с детьми? — Да, условия зависят от домика.\n"
            "• Где уточнить детали? — Через кнопку «Связаться с нами».",
        )

    rows = [[InlineKeyboardButton(text="✍️ Задать свой вопрос", callback_data="guest:feedback:start")]]
    rows.extend(build_showcase_section_rows("faq"))
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:showcase:location")
async def guest_showcase_location(callback: CallbackQuery):
    if not await ensure_guest_context(callback, "showcase"):
        return
    async with AsyncSessionLocal() as session:
        setting = await session.get(GlobalSetting, "coords")
        coords = setting.value if setting and setting.value else settings.project_coords

    async with AsyncSessionLocal() as session:
        location_text = await get_setting_value(
            session,
            "guest_showcase_location",
            f"📍 <b>Где мы находимся</b>\n\n"
            f"{settings.project_name} находится в {settings.project_location}.\n"
            f"Координаты: <code>{coords}</code>\n\n"
            "После авторизации будет доступен детальный маршрут до объекта.",
        )

    text = location_text
    rows = [[InlineKeyboardButton(text="📍 Открыть в Яндекс.Картах", url=f"https://yandex.ru/maps/?text={coords}")]]
    rows.extend(build_showcase_section_rows("location"))
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:feedback:start")
async def guest_feedback_start(callback: CallbackQuery):
    if not await ensure_guest_context(callback, "showcase"):
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗓 Бронирование", callback_data="guest:feedback:cat:booking")],
            [InlineKeyboardButton(text="🔑 Заселение", callback_data="guest:feedback:cat:checkin")],
            [InlineKeyboardButton(text="💳 Оплата", callback_data="guest:feedback:cat:payment")],
            [InlineKeyboardButton(text="❓ Другое", callback_data="guest:feedback:cat:other")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:showcase:faq")],
        ]
    )
    await callback.message.edit_text("Выберите тему вопроса:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("guest:feedback:cat:"))
async def guest_feedback_choose_category(callback: CallbackQuery):
    category = callback.data.split(":")[3]
    if category not in FEEDBACK_CATEGORIES:
        await callback.answer("Неизвестная категория", show_alert=True)
        return

    _feedback_waiting_users[callback.from_user.id] = category
    await callback.message.answer(
        f"✍️ Тема: <b>{FEEDBACK_CATEGORIES[category]}</b>\n"
        "Теперь напишите вопрос одним сообщением — я передам администратору.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(F.text)
async def guest_feedback_message(message: Message):
    if not message.from_user or message.from_user.id not in _feedback_waiting_users:
        return

    category = _feedback_waiting_users.pop(message.from_user.id)

    users = await get_all_users()
    admin_ids = {u.telegram_id for u in users if u.role in {UserRole.ADMIN, UserRole.OWNER} and u.telegram_id}
    admin_ids.add(settings.telegram_chat_id)

    text = (
        "📩 <b>Новый вопрос от гостя</b>\n\n"
        f"Тема: <b>{FEEDBACK_CATEGORIES.get(category, 'Другое')}</b>\n"
        f"От: {message.from_user.full_name} (@{message.from_user.username or '-'})\n"
        f"User ID: <code>{message.from_user.id}</code>\n\n"
        f"{message.text}"
    )

    for aid in admin_ids:
        try:
            await message.bot.send_message(aid, text, parse_mode="HTML")
        except Exception:
            pass

    await message.answer("✅ Спасибо! Передали вопрос администрации. Ответим как можно быстрее.")


@router.callback_query(F.data == "guest:my_booking")
async def my_booking(callback: CallbackQuery):
    if not await ensure_guest_auth(callback):
        return
    """Показать детали брони"""
    user_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        # 1. Получаем телефон пользователя
        user_result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user or not user.phone:
            await callback.answer(
                "❌ Ошибка авторизации. Телефон не найден.", show_alert=True
            )
            return

        # 2. Ищем бронь (активную)
        # Снова нечеткий поиск по телефону, или точный если мы уверены
        clean_user_phone = user.phone

        query = (
            select(Booking)
            .options(joinedload(Booking.house))
            .where(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PAID]))
        )
        result = await session.execute(query)
        bookings = result.scalars().all()

        found_booking = None
        for b in bookings:
            if phones_match(clean_user_phone, b.guest_phone):
                found_booking = b
                break

        if not found_booking:
            await callback.answer("❌ Активная бронь не найдена", show_alert=True)
            return

        # 3. Формируем карточку
        b = found_booking
        remainder = b.total_price - b.advance_amount
        status_emoji = "✅" if b.status == BookingStatus.PAID else "⏳"

        text = messages.booking_card(
            house_name=b.house.name,
            check_in=b.check_in.strftime("%d.%m"),
            check_out=b.check_out.strftime("%d.%m"),
            guests=b.guests_count,
            total=int(b.total_price),
            paid=int(b.advance_amount),
            remainder=int(remainder),
            status_emoji=status_emoji,
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Оплатить остаток", callback_data="guest:pay"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔑 Инструкция", callback_data="guest:instruction"
                    ),
                    InlineKeyboardButton(text="📶 Wi-Fi", callback_data="guest:wifi"),
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:menu")],
            ]
        )

        await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")


async def get_active_booking(session, user_id: int):
    """Помощник: ищет актуальную бронь для пользователя.

    Приоритет:
    1) Текущая/будущая бронь (check_out >= today) с ближайшим check_in
    2) Если таких нет — самая свежая по check_in
    """
    user_result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = user_result.scalar_one_or_none()

    if not user or not user.phone:
        return None

    clean_user_phone = user.phone

    query = (
        select(Booking)
        .options(joinedload(Booking.house))
        .where(
            Booking.status.in_(
                [
                    BookingStatus.CONFIRMED,
                    BookingStatus.PAID,
                    BookingStatus.CHECKING_IN,
                    BookingStatus.CHECKED_IN,
                ]
            )
        )
    )
    result = await session.execute(query)
    bookings = [b for b in result.scalars().all() if phones_match(clean_user_phone, b.guest_phone)]

    if not bookings:
        return None

    today = datetime.now().date()
    current_or_future = [b for b in bookings if b.check_out >= today]
    if current_or_future:
        current_or_future.sort(key=lambda x: x.check_in)
        return current_or_future[0]

    bookings.sort(key=lambda x: x.check_in, reverse=True)
    return bookings[0]


@router.callback_query(F.data == "guest:instruction")
async def guest_instruction(callback: CallbackQuery):
    if not await ensure_guest_auth(callback):
        return
    """Инструкция по заселению"""
    async with AsyncSessionLocal() as session:
        booking = await get_active_booking(session, callback.from_user.id)

        if not booking:
            await callback.answer("❌ Бронь не найдена", show_alert=True)
            return

        # Time-gate: инструкция доступна за 24 часа до заезда
        now = datetime.now().date()
        days_to_checkin = (booking.check_in - now).days
        if days_to_checkin > 1:
            await callback.message.edit_text(
                "🔒 <b>Инструкция будет доступна за 24 часа до заезда.</b>\n\n"
                f"До заезда осталось: <b>{days_to_checkin} дн.</b>",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="guest:my_booking")]]
                ),
                parse_mode="HTML",
            )
            await callback.answer()
            return

        instruction = (
            booking.house.checkin_instruction
            or "Инструкция формируется, свяжитесь с администратором."
        )

        text = (
            f"🔑 <b>Инструкция по заселению: {booking.house.name}</b>\n\n"
            f"{instruction}\n\n"
            "<i>(Эта информация доступна за 24ч до заезда)</i>"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="guest:my_booking"
                    )
                ],
            ]
        )
        await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "guest:wifi")
async def guest_wifi(callback: CallbackQuery):
    if not await ensure_guest_auth(callback):
        return
    """Wi-Fi"""
    async with AsyncSessionLocal() as session:
        booking = await get_active_booking(session, callback.from_user.id)

        if not booking:
            await callback.answer("❌ Бронь не найдена", show_alert=True)
            return

        wifi_info = booking.house.wifi_info or "Информация о Wi-Fi не задана."

        text = messages.wifi_info(booking.house.name, wifi_info)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="guest:my_booking"
                    )
                ],
            ]
        )
        await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "guest:directions")
async def guest_directions(callback: CallbackQuery):
    if not await ensure_guest_auth(callback):
        return
    """Как добраться"""
    async with AsyncSessionLocal() as session:
        # Получаем глобальные координаты
        setting = await session.get(GlobalSetting, "coords")
        coords = setting.value if setting and setting.value else settings.project_coords

        text = messages.directions(coords)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📍 Открыть в Яндекс.Картах",
                        url=f"https://yandex.ru/maps/?text={coords}",
                    )
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:menu")],
            ]
        )
        await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "guest:rules")
async def guest_rules(callback: CallbackQuery):
    if not await ensure_guest_auth(callback):
        return
    """Правила проживания"""
    async with AsyncSessionLocal() as session:
        # Получаем глобальные правила
        setting = await session.get(GlobalSetting, "rules")

        default_rules = (
            "1. Заезд после 14:00, выезд до 12:00.\n"
            "2. Соблюдайте тишину после 22:00.\n"
            "3. Курение в доме запрещено."
        )
        rules = setting.value if setting and setting.value else default_rules

        text = messages.rules_content(rules)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:menu")],
            ]
        )
        await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "guest:pay")
async def guest_pay(callback: CallbackQuery):
    if not await ensure_guest_auth(callback):
        return
    """Оплата"""
    async with AsyncSessionLocal() as session:
        booking = await get_active_booking(session, callback.from_user.id)
        amount = int(booking.total_price - booking.advance_amount) if booking else 0

    text = messages.payment_instructions(amount)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📸 Отправить чек оплаты", callback_data="guest:pay:receipt"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📞 Связаться с нами", callback_data="guest:contact_admin"
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:my_booking")],
        ]
    )
    await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "guest:pay:receipt")
async def guest_pay_receipt_start(callback: CallbackQuery):
    if not await ensure_guest_auth(callback):
        return
    async with AsyncSessionLocal() as session:
        booking = await get_active_booking(session, callback.from_user.id)
        if not booking:
            await callback.answer("❌ Активная бронь не найдена", show_alert=True)
            return

    _pay_receipt_waiting_users[callback.from_user.id] = booking.id
    await callback.message.answer(
        "📸 Отправьте фото чека одним сообщением.\n"
        "Можно добавить подпись (например: сумма/время оплаты)."
    )
    await callback.answer()


@router.message(F.photo)
async def guest_pay_receipt_photo(message: Message):
    if not message.from_user:
        return
    booking_id = _pay_receipt_waiting_users.get(message.from_user.id)
    if not booking_id:
        return

    _pay_receipt_waiting_users.pop(message.from_user.id, None)
    file_id = message.photo[-1].file_id
    caption = message.caption or "(без комментария)"

    users = await get_all_users()
    admin_ids = {u.telegram_id for u in users if u.role in {UserRole.ADMIN, UserRole.OWNER} and u.telegram_id}
    admin_ids.add(settings.telegram_chat_id)

    text = (
        f"💳 <b>Чек оплаты от гостя</b>\n\n"
        f"Гость: {message.from_user.full_name} (@{message.from_user.username or '-'})\n"
        f"Booking ID: <code>{booking_id}</code>\n"
        f"Комментарий: {caption}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"guest:pay:approve:{booking_id}:{message.from_user.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"guest:pay:reject:{booking_id}:{message.from_user.id}"),
        ]]
    )

    for aid in admin_ids:
        try:
            await message.bot.send_photo(aid, file_id, caption=text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass

    await message.answer("✅ Чек отправлен администратору на проверку.")


@router.callback_query(F.data.startswith("guest:pay:approve:"))
async def guest_pay_approve(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    _, _, _, booking_id_str, guest_tg_str = callback.data.split(":")
    booking_id = int(booking_id_str)
    guest_tg = int(guest_tg_str)

    async with AsyncSessionLocal() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Бронь не найдена", show_alert=True)
            return
        booking.status = BookingStatus.PAID
        booking.advance_amount = booking.total_price
        await session.commit()

    try:
        await callback.bot.send_message(guest_tg, "✅ Оплата подтверждена. Спасибо!")
    except Exception:
        pass
    await callback.answer("Оплата подтверждена")


@router.callback_query(F.data.startswith("guest:pay:reject:"))
async def guest_pay_reject(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    _, _, _, booking_id_str, guest_tg_str = callback.data.split(":")
    booking_id = int(booking_id_str)
    guest_tg = int(guest_tg_str)

    try:
        await callback.bot.send_message(
            guest_tg,
            f"⚠️ Чек по брони #{booking_id} отклонён. Пожалуйста, свяжитесь с администратором.",
        )
    except Exception:
        pass
    await callback.answer("Чек отклонён")


@router.callback_query(F.data == "guest:logout")
async def guest_logout(callback: CallbackQuery):
    removed = await remove_guest_user(callback.from_user.id)
    if callback.from_user:
        set_guest_auth(callback.from_user.id, False)
        set_guest_context(callback.from_user.id, "showcase")

    text = (
        "✅ Вы вышли из гостевого кабинета."
        if removed
        else "ℹ️ Вы уже не авторизованы как гость."
    )

    await callback.message.edit_text(
        f"{text}\n\n"
        f"🏕 <b>{settings.project_name}</b> — место для отдыха в {settings.project_location}.\n"
        "Выберите, что хотите посмотреть:",
        reply_markup=guest_showcase_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "guest:partners")
async def guest_partners(callback: CallbackQuery):
    if not await ensure_guest_auth(callback):
        return
    if not settings.guest_feature_partners:
        await callback.answer("Раздел партнёров временно недоступен", show_alert=True)
        return
    async with AsyncSessionLocal() as session:
        partners_text = await get_setting_value(
            session,
            "guest_partners_v1",
            "🤝 <b>Партнёры</b>\n\n"
            "<b>Инструкторы</b> — обучение/сопровождение на склонах.\n"
            "<b>Квадроциклы</b> — маршруты и прокат по согласованию.\n"
            "<b>Активности</b> — подскажем, чем заняться в Архызе.\n\n"
            "Чтобы подобрать вариант под даты проживания — отправьте запрос администратору.",
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📞 Запросить через администратора", callback_data="guest:contact_admin")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:menu")],
        ]
    )
    await callback.message.edit_text(partners_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:contact_admin")
async def contact_admin(callback: CallbackQuery):

    # Тут можно дать ссылку на админа
    await callback.message.answer(
        messages.CONTACT_ADMIN,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "guest:showcase:menu")
async def back_to_showcase_menu(callback: CallbackQuery):
    if not await ensure_guest_context(callback, "showcase"):
        return
    """Гарантированный возврат в витрину (для unauth flow)."""
    if callback.from_user:
        set_guest_context(callback.from_user.id, "showcase")
    await safe_edit(
        callback,
        f"🏕 <b>{settings.project_name}</b> — место для отдыха в {settings.project_location}.\n\n"
        "Выберите, что хотите посмотреть:",
        reply_markup=guest_showcase_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "guest:menu")
async def back_to_guest_menu(callback: CallbackQuery):
    """Возврат в главное меню (витрина или кабинет)."""
    if is_guest_authorized(callback.from_user.id):
        set_guest_context(callback.from_user.id, "guest_cabinet")
        await safe_edit(
            callback,
            messages.GUEST_WELCOME,
            reply_markup=guest_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        set_guest_context(callback.from_user.id, "showcase")
        await safe_edit(
            callback,
            f"🏕 <b>{settings.project_name}</b> — место для отдыха в {settings.project_location}.\n\n"
            "Выберите, что хотите посмотреть:",
            reply_markup=guest_showcase_menu_keyboard(),
            parse_mode="HTML",
        )
    await callback.answer()
