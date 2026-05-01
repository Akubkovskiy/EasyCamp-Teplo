import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
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
from app.services.booking_service import BookingService
from app.services.notification_service import send_safe

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
            f"🏕 <b>{settings.project_name}</b> — база отдыха рядом с Архызом\n\n"
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
        f"🏕 <b>{settings.project_name}</b> — база отдыха рядом с Архызом\n\n"
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
            f"🏕 <b>{settings.project_name}</b> — база отдыха рядом с Архызом\n\n"
            "Выберите, что хотите посмотреть:",
            reply_markup=guest_showcase_menu_keyboard(),
            parse_mode="HTML",
        )


# -------------------------------------------------
# Slash-команды для Bot Menu (кнопка Menu)
# -------------------------------------------------


@router.message(Command("about"))
async def cmd_about(message: Message):
    """Команда /about — О базе отдыха."""
    async with AsyncSessionLocal() as session:
        about_text = await get_setting_value(
            session,
            "guest_showcase_about",
            f"<b>{settings.project_name}</b> — база отдыха рядом с Архызом, "
            "в спокойной локации немного в стороне от посёлка.\n\n"
            "На территории 3 домика для 2–6 гостей. Во всех есть Wi-Fi, горячая вода, "
            "постельное бельё, полотенца, кухня с посудой, мангал и парковка.\n\n"
            "Подойдёт тем, кто хочет отдыхать не в центре, а в более тихом месте "
            "недалеко от курорта и горных маршрутов.",
        )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="guest:showcase:menu")]]
    )
    await message.answer(about_text, reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("dates"))
async def cmd_dates(message: Message):
    """Команда /dates — проверить свободные даты (запускает availability flow)."""
    from app.telegram.handlers.availability import availability_command
    await availability_command(message)


@router.message(Command("location"))
async def cmd_location(message: Message):
    """Команда /location — Где мы находимся."""
    async with AsyncSessionLocal() as session:
        setting = await session.get(GlobalSetting, "coords")
        coords = setting.value if setting and setting.value else settings.project_coords

        location_text = await get_setting_value(
            session,
            "guest_showcase_location",
            f"📍 <b>Где мы находимся</b>\n\n"
            f"{settings.project_name} расположена рядом с Архызом, в спокойной локации "
            "немного в стороне от посёлка.\n\n"
            f"Координаты для навигатора:\n<code>{coords}</code>",
        )

    rows = [[InlineKeyboardButton(text="📍 Открыть в Яндекс.Картах", url=f"https://yandex.ru/maps/?text={coords}")]]
    rows.append([InlineKeyboardButton(text="🔙 Меню", callback_data="guest:showcase:menu")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.answer(location_text, reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("contact"))
async def cmd_contact(message: Message):
    """Команда /contact — Связаться с нами."""
    await message.answer(messages.CONTACT_ADMIN, parse_mode="HTML")


@router.message(Command("login"))
async def cmd_login(message: Message):
    """Команда /login — Авторизоваться по брони."""
    user_id = message.from_user.id
    if is_guest_authorized(user_id):
        await message.answer("✅ Вы уже авторизованы.")
        await show_guest_menu(message)
        return

    await message.answer(
        messages.GUEST_LOGIN_PROMPT,
        reply_markup=request_contact_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("booking"))
async def cmd_booking(message: Message):
    """Команда /booking — Моя бронь."""
    user_id = message.from_user.id
    if not is_guest_authorized(user_id):
        await message.answer(
            "🔐 Сначала авторизуйтесь, чтобы посмотреть свою бронь.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔐 Авторизоваться", callback_data="guest:auth")]]
            ),
        )
        return

    async with AsyncSessionLocal() as session:
        booking = await get_active_booking(session, user_id)
        if not booking:
            await message.answer("❌ Активная бронь не найдена.")
            return

        house = booking.house
        text = messages.booking_card(
            house_name=house.name if house else "—",
            check_in=booking.check_in,
            check_out=booking.check_out,
            guests_count=booking.guests_count,
            total_price=int(booking.total_price) if booking.total_price else 0,
            advance_amount=int(booking.advance_amount) if booking.advance_amount else 0,
            status=booking.status,
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="guest:menu")]]
        )
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


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
            f"<b>{settings.project_name}</b> — база отдыха рядом с Архызом, "
            "в спокойной локации немного в стороне от посёлка.\n\n"
            "На территории 3 домика для 2–6 гостей. Во всех есть Wi-Fi, горячая вода, "
            "постельное бельё, полотенца, кухня с посудой, мангал и парковка.\n\n"
            "Подойдёт тем, кто хочет отдыхать не в центре, а в более тихом месте "
            "недалеко от курорта и горных маршрутов.",
        )
    keyboard = InlineKeyboardMarkup(inline_keyboard=build_showcase_section_rows("about"))
    await safe_edit(callback, about_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:showcase:houses")
async def guest_showcase_houses(callback: CallbackQuery):
    if not await ensure_guest_context(callback, "showcase"):
        return

    from app.services.house_service import HouseService
    from app.services.pricing_service import PricingService
    from app.data.house_descriptions import get_display_description

    async with AsyncSessionLocal() as db:
        houses = await HouseService.get_all_houses(db)

        if not houses:
            text = "🏕 <b>Наши домики</b>\n\nИнформация о домиках скоро появится."
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=build_showcase_section_rows("houses")
            )
            await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
            return

        text = "🏕 <b>Наши домики</b>\n\n"
        for house in houses:
            price_info = await PricingService.get_display_price(db, house.id)
            price = price_info["final_price"]
            base = price_info["price"]

            desc = get_display_description(house.name, house.description)

            text += f"🏠 <b>{house.name}</b>  ·  до {house.capacity} гостей\n"
            if desc:
                text += f"{desc}\n"
            if price:
                if price_info["discount_percent"]:
                    text += (
                        f"💰 <b>{price:,} ₽/сут</b>  <s>{base:,} ₽</s>"
                        f"  <i>−{price_info['discount_percent']}%</i>\n"
                    )
                else:
                    text += f"💰 от <b>{price:,} ₽/сут</b>\n"
            text += "\n"

    keyboard_rows = []
    for house in houses:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"🏠 {house.name}",
                callback_data=f"guest:house:{house.id}",
            )
        ])
    keyboard_rows.extend(build_showcase_section_rows("houses"))

    await safe_edit(
        callback, text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("guest:house:"))
async def guest_house_detail(callback: CallbackQuery):
    """Детальная карточка домика с фото"""
    if not await ensure_guest_context(callback, "showcase"):
        return

    house_id = int(callback.data.split(":")[2])

    from app.services.house_service import HouseService
    from app.services.pricing_service import PricingService
    from app.data.house_descriptions import get_full_description

    async with AsyncSessionLocal() as db:
        house = await HouseService.get_house_by_id(db, house_id)
        if not house:
            await callback.answer("Домик не найден")
            return

        price_info = await PricingService.get_display_price(db, house.id)

    price = price_info["final_price"]
    base = price_info["price"]

    text = f"🏠 <b>{house.name}</b>\n\n"
    text += f"👥 Вместимость: до {house.capacity} гостей\n"

    # Полное описание: promo > БД > файл описаний
    full_desc = house.promo_description or house.description or get_full_description(house.name)
    if full_desc:
        text += f"\n{full_desc}\n"

    if price:
        text += "\n💰 <b>Стоимость:</b> "
        if price_info["discount_percent"]:
            text += (
                f"<s>{base} ₽</s> → <b>{price} ₽/сут</b> "
                f"(-{price_info['discount_percent']}%)\n"
            )
        else:
            text += f"от <b>{price} ₽/сут</b>\n"

        if price_info["season_label"]:
            text += f"📅 Сезон: {price_info['season_label']}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Забронировать", callback_data="guest:availability")],
        [InlineKeyboardButton(text="🔙 Все домики", callback_data="guest:showcase:houses")],
    ])

    # Если есть фото — отправляем с фото
    if house.promo_image_id:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer_photo(
            photo=house.promo_image_id,
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    else:
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
            f"{settings.project_name} расположена рядом с Архызом, в спокойной локации "
            "немного в стороне от посёлка.\n\n"
            f"Координаты для навигатора:\n<code>{coords}</code>",
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


@router.message(StateFilter(None), F.text)
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
        await send_safe(message.bot, aid, text, context=f"guest_feedback admin={aid}")

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

        # G10.5 polish: для PAID скрываем «оплатить остаток», показываем
        # «✅ Полностью оплачено» (дисэйблнутая кнопка-метка).
        is_fully_paid = (
            b.status == BookingStatus.PAID
            and remainder <= 0
        )
        if is_fully_paid:
            pay_row = [
                InlineKeyboardButton(
                    text="✅ Оплата подтверждена", callback_data="guest:pay"
                )
            ]
        else:
            pay_row = [
                InlineKeyboardButton(
                    text="💳 Оплатить остаток", callback_data="guest:pay"
                )
            ]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                pay_row,
                [
                    InlineKeyboardButton(
                        text="🔑 Инструкция", callback_data="guest:instruction"
                    ),
                    InlineKeyboardButton(text="📶 Wi-Fi", callback_data="guest:wifi"),
                ],
                [
                    InlineKeyboardButton(
                        text="🚫 Отменить бронь",
                        callback_data=f"guest:cancel:start:{b.id}",
                    )
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
    """Инструкция по заселению (time-gate настраивается через GlobalSetting
    `guest_instruction_open_hours`, default 24)."""
    from datetime import time as dtime

    from app.services.global_settings import (
        get_guest_instruction_open_hours,
        is_instruction_open,
    )

    async with AsyncSessionLocal() as session:
        booking = await get_active_booking(session, callback.from_user.id)

        if not booking:
            await callback.answer("❌ Бронь не найдена", show_alert=True)
            return

        open_hours = await get_guest_instruction_open_hours(session)

        check_in_dt = datetime.combine(booking.check_in, dtime.min)
        hours_to_checkin = (check_in_dt - datetime.now()).total_seconds() / 3600

        if not is_instruction_open(hours_to_checkin, open_hours):
            # Считаем «дней до заезда» для UX-сообщения
            days_to_checkin = max(0, int(hours_to_checkin // 24))
            await callback.message.edit_text(
                f"🔒 <b>Инструкция будет доступна за {open_hours} ч до заезда.</b>\n\n"
                f"До заезда осталось: <b>~{days_to_checkin} дн.</b>",
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
            f"<i>(Эта информация открывается за {open_hours} ч до заезда)</i>"
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
    """Оплата — двухэтапная (G10.6): задаток при бронировании + остаток
    при заселении. Текущая стадия определяется по advance_amount."""
    from app.services.global_settings import (
        compute_advance_amount,
        get_guest_advance_percent,
        payment_stage,
    )

    async with AsyncSessionLocal() as session:
        booking = await get_active_booking(session, callback.from_user.id)
        advance_percent = await get_guest_advance_percent(session)

    if not booking:
        await callback.answer("❌ Активная бронь не найдена", show_alert=True)
        return

    total = int(booking.total_price or 0)
    paid = int(booking.advance_amount or 0)
    required_advance = compute_advance_amount(total, advance_percent)
    stage = payment_stage(total, paid, required_advance)
    remainder = max(0, total - paid)

    if stage == "fully_paid":
        paid_at = (
            booking.updated_at.strftime("%d.%m.%Y %H:%M")
            if getattr(booking, "updated_at", None)
            else "—"
        )
        text = (
            "✅ <b>Оплата подтверждена полностью</b>\n\n"
            f"Оплачено: <b>{paid:,} ₽</b>\n"
            f"Дата: <b>{paid_at}</b>\n\n"
            "Если у вас вопросы — напишите администратору."
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📞 Связаться с нами",
                        callback_data="guest:contact_admin",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="guest:my_booking"
                    )
                ],
            ]
        )
        await safe_edit(callback, text, reply_markup=keyboard, parse_mode="HTML")
        return

    if stage == "advance_paid":
        # задаток внесён, ждём остаток (вносится при заезде)
        text = (
            "💳 <b>Доплата при заселении</b>\n\n"
            f"Всего: <b>{total:,} ₽</b>\n"
            f"Задаток внесён: <b>{paid:,} ₽</b> ✅\n"
            f"К доплате при заезде: <b>{remainder:,} ₽</b>\n\n"
            "Сумму остатка можно перевести по тем же реквизитам:\n"
            f"<code>{settings.contact_phone}</code> ({settings.payment_methods})\n"
            f"Получатель: {settings.payment_receiver}\n\n"
            "После перевода пришлите чек — мы подтвердим."
        )
        button_text = "📸 Отправить чек остатка"
    else:
        # стадия no_payment — гость должен внести задаток
        if required_advance > 0:
            text = (
                "💰 <b>Внесите задаток</b>\n\n"
                f"Всего: <b>{total:,} ₽</b>\n"
                f"Задаток ({advance_percent}%): <b>{required_advance:,} ₽</b>\n"
                f"Остаток оплачивается при заезде: {total - required_advance:,} ₽\n\n"
                f"Переведите задаток по реквизитам:\n"
                f"<code>{settings.contact_phone}</code> ({settings.payment_methods})\n"
                f"Получатель: {settings.payment_receiver}\n\n"
                "После перевода пришлите чек — мы подтвердим."
            )
            button_text = "📸 Отправить чек задатка"
        else:
            # special case: нулевой процент задатка → сразу полная оплата
            text = messages.payment_instructions(remainder)
            button_text = "📸 Отправить чек оплаты"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button_text, callback_data="guest:pay:receipt"
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
        "📸 Отправьте фото чека или PDF-выписку из банка одним сообщением.\n"
        "Можно добавить подпись (например: сумма/время оплаты)."
    )
    await callback.answer()


def _is_pay_receipt_waiting(message: Message) -> bool:
    """Filter: гость находится в режиме ожидания чека (нажал «Отправить чек»)."""
    return bool(
        message.from_user
        and message.from_user.id in _pay_receipt_waiting_users
    )


async def _send_pay_receipt_to_admins(
    message: Message,
    booking_id: int,
    file_id: str,
    is_photo: bool,
):
    """Общая логика для photo и document: уведомить админов с inline-кнопками
    задатка / полной оплаты / отклонения (G10.6)."""
    from app.services.global_settings import (
        compute_advance_amount,
        get_guest_advance_percent,
    )

    users = await get_all_users()
    admin_ids = {u.telegram_id for u in users if u.role in {UserRole.ADMIN, UserRole.OWNER} and u.telegram_id}
    admin_ids.add(settings.telegram_chat_id)

    # Подтянем актуальные данные брони + рассчёт задатка для подсказки в кнопке
    advance_btn_label = "✅ Задаток"
    full_btn_label = "✅ Полная оплата"
    info_lines = []
    async with AsyncSessionLocal() as session:
        booking = await session.get(Booking, booking_id)
        percent = await get_guest_advance_percent(session)
        if booking:
            total_i = int(booking.total_price or 0)
            paid_i = int(booking.advance_amount or 0)
            required_advance = compute_advance_amount(total_i, percent)
            remainder = max(0, total_i - paid_i)
            info_lines.append(f"Всего: {total_i:,} ₽")
            info_lines.append(f"Уже оплачено: {paid_i:,} ₽")
            info_lines.append(f"Задаток ({percent}%): {required_advance:,} ₽")
            info_lines.append(f"Остаток: {remainder:,} ₽")
            advance_btn_label = f"✅ Задаток ({required_advance:,} ₽)"
            full_btn_label = f"✅ Полная (+{remainder:,} ₽)"

    caption_user = message.caption or "(без комментария)"
    text = (
        f"💳 <b>Чек оплаты от гостя</b>\n\n"
        f"Гость: {message.from_user.full_name} (@{message.from_user.username or '-'})\n"
        f"Booking ID: <code>{booking_id}</code>\n"
        + ("\n".join(info_lines) + "\n\n" if info_lines else "")
        + f"Комментарий: {caption_user}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=advance_btn_label,
                    callback_data=f"guest:pay:approve_advance:{booking_id}:{message.from_user.id}",
                ),
                InlineKeyboardButton(
                    text=full_btn_label,
                    callback_data=f"guest:pay:approve_full:{booking_id}:{message.from_user.id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"guest:pay:reject:{booking_id}:{message.from_user.id}",
                ),
            ],
        ]
    )

    for aid in admin_ids:
        try:
            if is_photo:
                await message.bot.send_photo(aid, file_id, caption=text, reply_markup=kb, parse_mode="HTML")
            else:
                await message.bot.send_document(aid, file_id, caption=text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass


@router.message(F.photo, _is_pay_receipt_waiting)
async def guest_pay_receipt_photo(message: Message):
    booking_id = _pay_receipt_waiting_users.get(message.from_user.id)
    if not booking_id:
        return

    _pay_receipt_waiting_users.pop(message.from_user.id, None)
    file_id = message.photo[-1].file_id

    await _send_pay_receipt_to_admins(message, booking_id, file_id, is_photo=True)
    await message.answer("✅ Чек отправлен администратору на проверку.")


@router.message(F.document, _is_pay_receipt_waiting)
async def guest_pay_receipt_document(message: Message):
    """PDF / любая выписка из банка как document. Принимаем pdf/jpeg/png по
    `mime_type`, остальные документы вежливо отклоняем."""
    booking_id = _pay_receipt_waiting_users.get(message.from_user.id)
    if not booking_id:
        return

    doc = message.document
    if not doc:
        return

    allowed_mimes = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/heic",
        "image/webp",
    }
    if doc.mime_type and doc.mime_type not in allowed_mimes:
        await message.answer(
            "⚠️ Поддерживаются только PDF и изображения (jpg/png). "
            f"Вы отправили: <code>{doc.mime_type}</code>. "
            "Пришлите фото чека или PDF-выписку.",
            parse_mode="HTML",
        )
        return

    _pay_receipt_waiting_users.pop(message.from_user.id, None)
    await _send_pay_receipt_to_admins(message, booking_id, doc.file_id, is_photo=False)
    await message.answer("✅ Чек отправлен администратору на проверку.")


async def _admin_approve_payment(
    callback: CallbackQuery,
    *,
    full_payment: bool,
):
    from app.services.global_settings import get_guest_advance_percent

    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    parts = callback.data.split(":")
    # callback: guest:pay:approve_advance:{id}:{tg} OR guest:pay:approve_full:{id}:{tg}
    # OR legacy: guest:pay:approve:{id}:{tg}
    try:
        booking_id = int(parts[-2])
        guest_tg = int(parts[-1])
    except (IndexError, ValueError):
        await callback.answer("Bad callback", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        percent = await get_guest_advance_percent(session)
        booking, label, became_paid = await BookingService.record_payment(
            session, booking_id, full_payment=full_payment, advance_percent=percent
        )

    if booking is None:
        await callback.answer("Бронь не найдена", show_alert=True)
        return

    if became_paid:
        from app.services.cleaner_notify import notify_cleaners_new_booking
        await notify_cleaners_new_booking(callback.bot, booking)

    pay_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Моя бронь", callback_data="guest:my_booking")],
        ]
    )
    await send_safe(callback.bot, guest_tg, label, reply_markup=pay_kb, context=f"pay_approve guest={guest_tg}")

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.answer("Готово")


@router.callback_query(F.data.startswith("guest:pay:approve_advance:"))
async def guest_pay_approve_advance(callback: CallbackQuery):
    await _admin_approve_payment(callback, full_payment=False)


@router.callback_query(F.data.startswith("guest:pay:approve_full:"))
async def guest_pay_approve_full(callback: CallbackQuery):
    await _admin_approve_payment(callback, full_payment=True)


# Legacy callback (старые уведомления админам, отправленные до G10.6 deploy)
# трактуем как «полная оплата» — оригинальное поведение.
@router.callback_query(F.data.startswith("guest:pay:approve:"))
async def guest_pay_approve_legacy(callback: CallbackQuery):
    await _admin_approve_payment(callback, full_payment=True)


@router.callback_query(F.data.startswith("guest:pay:reject:"))
async def guest_pay_reject(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    _, _, _, booking_id_str, guest_tg_str = callback.data.split(":")
    booking_id = int(booking_id_str)
    guest_tg = int(guest_tg_str)

    await send_safe(
        callback.bot, guest_tg,
        f"⚠️ Чек по брони #{booking_id} отклонён. Пожалуйста, свяжитесь с администратором.",
        context=f"pay_reject guest={guest_tg}",
    )
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
    from app.telegram.handlers.contacts import _contacts_keyboard
    back = "guest:menu" if is_guest(callback.from_user.id) else "guest:showcase:menu"
    await callback.message.answer(
        messages.CONTACTS_INFO,
        reply_markup=_contacts_keyboard(back),
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
        messages.GUEST_WELCOME,
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
            f"🏕 <b>{settings.project_name}</b> — база отдыха рядом с Архызом\n\n"
            "Выберите, что хотите посмотреть:",
            reply_markup=guest_showcase_menu_keyboard(),
            parse_mode="HTML",
        )
    await callback.answer()
