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
from app.telegram.menus.guest import guest_menu_keyboard, request_contact_keyboard

router = Router()
logger = logging.getLogger(__name__)


async def show_guest_menu(message: Message):
    """Показывает меню гостя (или запрос контакта)"""
    user_id = message.from_user.id

    # 1. Если авторизован -> Главное меню
    if is_guest(user_id):
        await message.answer(
            "🏕 <b>Добро пожаловать домой!</b>\n\n"
            "Вы в меню гостя. Здесь вся информация о вашем отдыхе.",
            reply_markup=guest_menu_keyboard(),
            parse_mode="HTML",
        )
    # 2. Если нет -> Просим контакт
    else:
        await message.answer(
            "👋 <b>Добрый день!</b>\n\n"
            "Чтобы увидеть детали своего бронирования, пожалуйста, подтвердите номер телефона.",
            reply_markup=request_contact_keyboard(),
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
                "✅ <b>Бронь найдена!</b>\n"
                f"Мы рады видеть вас, {message.from_user.first_name}!",
                reply_markup=ReplyKeyboardRemove(),  # Убираем кнопку контакта
            )
            await show_guest_menu(message)

        else:
            # НЕ НАЙДЕНО
            await message.answer(
                "❌ <b>Бронь не найдена.</b>\n\n"
                "Мы не нашли активных бронирований на этот номер.\n"
                "Если вы бронировали через Avito, возможно, там указан другой (подменный) номер.\n\n"
                "Пожалуйста, свяжитесь с администратором.",
                reply_markup=ReplyKeyboardRemove(),
            )


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

        text = (
            f"🏠 <b>Ваша бронь: {b.house.name}</b>\n\n"
            f"📅 <b>Даты:</b> {b.check_in.strftime('%d.%m')} — {b.check_out.strftime('%d.%m')}\n"
            f"👤 <b>Гости:</b> {b.guests_count}\n\n"
            f"💰 <b>Финансы:</b>\n"
            f"Всего: {int(b.total_price)}₽\n"
            f"Оплачено: {int(b.advance_amount)}₽\n"
            f"<b>К оплате: {int(remainder)}₽</b> {status_emoji}\n\n"
            f"📍 <b>Адрес:</b> Архыз, Банковская 26д\n"
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

        text = f"📶 <b>Wi-Fi: {booking.house.name}</b>\n\n{wifi_info}\n"
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
        coords = setting.value if setting and setting.value else "43.560731, 41.284236"

        text = (
            f"🗺 <b>Как добраться</b>\n\n"
            "📍 <b>Адрес:</b> с. Архыз, ул. Банковская, 26д\n\n"
            "Мы находимся в живописном месте, окруженном горами.\n"
            f"Координаты для навигатора:\n<code>{coords}</code>\n"
        )

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

        text = f"ℹ️ <b>Правила проживания</b>\n\n{rules}\n"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="guest:menu")],
            ]
        )
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "guest:pay")
async def guest_pay(callback: CallbackQuery):
    """Оплата"""
    text = (
        "💳 <b>Оплата бронирования</b>\n\n"
        "Для оплаты остатка, пожалуйста, переведите сумму по номеру телефона:\n"
        "<code>+7 928 000-00-00</code> (Сбер/Тинькофф)\n"
        "Получатель: Сергей Иванович П.\n\n"
        "После перевода отправьте чек администратору."
    )
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


@router.callback_query(F.data == "guest:contact_admin")
async def contact_admin(callback: CallbackQuery):

    # Тут можно дать ссылку на админа
    await callback.message.answer(
        "📞 <b>Связь с администратором</b>\n\n"
        "Если у вас возникли вопросы, напишите нам @sergey_teplo (пример).",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "guest:menu")
async def back_to_guest_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🏕 <b>Добро пожаловать домой!</b>\n\n"
        "Вы в меню гостя. Здесь вся информация о вашем отдыхе.",
        reply_markup=guest_menu_keyboard(),
        parse_mode="HTML",
    )
