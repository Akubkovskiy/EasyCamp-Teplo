import logging
import re
from aiogram import Router, F
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
from app.models import Booking, BookingStatus, UserRole, User, GlobalSetting
from app.telegram.auth.admin import add_user, is_guest
from app.telegram.menus.guest import (
    guest_menu_keyboard,
    guest_showcase_menu_keyboard,
    request_contact_keyboard,
)
from app.core.messages import messages
from app.core.config import settings

router = Router()
logger = logging.getLogger(__name__)


async def show_guest_menu(message: Message):
    """Показывает меню гостя: витрина (unauth) или кабинет (auth)."""
    user_id = message.from_user.id

    if is_guest(user_id):
        await message.answer(
            messages.GUEST_WELCOME,
            reply_markup=guest_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
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

    # Нормализация телефона (удаляем лишнее, приводим к виду 79...)
    phone = contact.phone_number
    clean_phone = re.sub(r"[\+\(\)\-\s]", "", phone)

    if clean_phone.startswith("8"):
        clean_phone = "7" + clean_phone[1:]

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
            b_phone = re.sub(r"[\+\(\)\-\s]", "", booking.guest_phone)
            if b_phone.startswith("8"):
                b_phone = "7" + b_phone[1:]

            # Сравниваем (учитываем что clean_phone может быть без 7 или +7)
            if clean_phone in b_phone or b_phone in clean_phone:
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

            await message.answer(
                messages.welcome_success(message.from_user.first_name),
                reply_markup=ReplyKeyboardRemove(),  # Убираем кнопку контакта
            )
            await show_guest_menu(message)

        else:
            # НЕ НАЙДЕНО
            await message.answer(
                messages.BOOKING_NOT_FOUND,
                reply_markup=ReplyKeyboardRemove(),
            )


@router.callback_query(F.data == "guest:auth")
async def guest_auth_prompt(callback: CallbackQuery):
    """Попросить контакт для авторизации по брони."""
    await callback.message.answer(
        messages.GUEST_LOGIN_PROMPT,
        reply_markup=request_contact_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "guest:showcase:about")
async def guest_showcase_about(callback: CallbackQuery):
    text = (
        f"🏕 <b>{settings.project_name}</b>\n\n"
        f"Мы находимся в {settings.project_location}. Уютные домики, природа и спокойный отдых.\n"
        "Выберите следующий раздел, чтобы посмотреть домики, даты и условия."
    )
    await callback.message.edit_text(text, reply_markup=guest_showcase_menu_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:showcase:houses")
async def guest_showcase_houses(callback: CallbackQuery):
    text = (
        "🏠 <b>Домики и фото</b>\n\n"
        "Раздел в доработке: скоро здесь будет галерея по каждому домику с фото и описанием.\n"
        "Пока можно проверить даты и перейти к бронированию."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Проверить даты и забронировать", callback_data="guest:availability")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:menu")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:showcase:faq")
async def guest_showcase_faq(callback: CallbackQuery):
    text = (
        "❓ <b>Популярные вопросы</b>\n\n"
        "• Как забронировать? — Нажмите «Проверить даты и забронировать».\n"
        "• Когда заезд/выезд? — Обычно заезд после 14:00, выезд до 12:00.\n"
        "• Можно с детьми? — Да, условия зависят от домика.\n"
        "• Где уточнить детали? — Через кнопку «Связаться с нами»."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📞 Задать свой вопрос", callback_data="guest:contact_admin")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:menu")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:showcase:location")
async def guest_showcase_location(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        setting = await session.get(GlobalSetting, "coords")
        coords = setting.value if setting and setting.value else settings.project_coords

    text = (
        f"📍 <b>Где мы находимся</b>\n\n"
        f"{settings.project_name} находится в {settings.project_location}.\n"
        f"Координаты: <code>{coords}</code>\n\n"
        "После авторизации будет доступен детальный маршрут до объекта."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 Открыть в Яндекс.Картах", url=f"https://yandex.ru/maps/?text={coords}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:menu")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:my_booking")
async def my_booking(callback: CallbackQuery):
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
            b_phone = re.sub(r"[\+\(\)\-\s]", "", b.guest_phone)
            if b_phone.startswith("8"):
                b_phone = "7" + b_phone[1:]

            if clean_user_phone in b_phone or b_phone in clean_user_phone:
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

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


async def get_active_booking(session, user_id: int):
    """Помощник: ищет активную бронь для пользователя"""
    user_result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = user_result.scalar_one_or_none()

    if not user or not user.phone:
        return None

    clean_user_phone = user.phone

    query = (
        select(Booking)
        .options(joinedload(Booking.house))
        .where(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PAID]))
    )
    result = await session.execute(query)
    bookings = result.scalars().all()

    for b in bookings:
        b_phone = re.sub(r"[\+\(\)\-\s]", "", b.guest_phone)
        if b_phone.startswith("8"):
            b_phone = "7" + b_phone[1:]

        if clean_user_phone in b_phone or b_phone in clean_user_phone:
            return b
    return None


@router.callback_query(F.data == "guest:instruction")
async def guest_instruction(callback: CallbackQuery):
    """Инструкция по заселению"""
    async with AsyncSessionLocal() as session:
        booking = await get_active_booking(session, callback.from_user.id)

        if not booking:
            await callback.answer("❌ Бронь не найдена", show_alert=True)
            return

        # TODO: Проверка времени (за 24ч до заезда)

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
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "guest:wifi")
async def guest_wifi(callback: CallbackQuery):
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
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "guest:directions")
async def guest_directions(callback: CallbackQuery):
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
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "guest:rules")
async def guest_rules(callback: CallbackQuery):
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
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "guest:pay")
async def guest_pay(callback: CallbackQuery):
    """Оплата"""
    async with AsyncSessionLocal() as session:
        booking = await get_active_booking(session, callback.from_user.id)
        amount = int(booking.total_price - booking.advance_amount) if booking else 0

    text = messages.payment_instructions(amount)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📞 Отправить чек админу", callback_data="guest:contact_admin"
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:my_booking")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "guest:partners")
async def guest_partners(callback: CallbackQuery):
    text = (
        "🤝 <b>Партнёры</b>\n\n"
        "Скоро здесь появятся проверенные партнёры: инструкторы, квадроциклы и активности.\n"
        "Пока можно оставить запрос через администратора."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📞 Запросить через администратора", callback_data="guest:contact_admin")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:menu")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "guest:contact_admin")
async def contact_admin(callback: CallbackQuery):

    # Тут можно дать ссылку на админа
    await callback.message.answer(
        messages.CONTACT_ADMIN,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "guest:menu")
async def back_to_guest_menu(callback: CallbackQuery):
    """Возврат в главное меню (витрина или кабинет)."""
    if is_guest(callback.from_user.id):
        await callback.message.edit_text(
            messages.GUEST_WELCOME,
            reply_markup=guest_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            f"🏕 <b>{settings.project_name}</b> — место для отдыха в {settings.project_location}.\n\n"
            "Выберите, что хотите посмотреть:",
            reply_markup=guest_showcase_menu_keyboard(),
            parse_mode="HTML",
        )
    await callback.answer()
