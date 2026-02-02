from datetime import date, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus
from app.core.config import settings
from app.jobs.avito_sync_job import sync_avito_job

router = Router()

# LEGACY BOOKING FLOW - DISABLED
# This old booking flow conflicts with the new FSM-based flow in booking_management/create.py
# The @router.message(F.text) handler is too broad and intercepts all text messages
# Keeping the code commented for reference, but it should be removed or refactored

# @router.callback_query(lambda c: c.data and c.data.startswith("booking:create:"))
# async def start_booking_from_availability(callback: CallbackQuery):
#     """Начало процесса бронирования из проверки доступности"""
#     if callback.from_user is None or callback.message is None or callback.data is None:
#         return
#
#     user_id = callback.from_user.id
#     _, _, house_id_str = callback.data.split(":")
#     house_id = int(house_id_str)
#
#     # Получаем состояние доступности
#     state = availability_states.get(user_id)
#     if not state or not state.check_in or not state.check_out:
#         await callback.answer("❌ Ошибка: даты не найдены. Попробуйте снова.", show_alert=True)
#         return
#
#     # Получаем информацию о доме
#     from app.services.house_service import house_service
#     house = await house_service.get_house(house_id)
#     if not house:
#         await callback.answer("❌ Домик не найден", show_alert=True)
#         return
#
#     # Вычисляем количество ночей и стоимость
#     nights = (state.check_out - state.check_in).days
#
#     # Сохраняем данные бронирования в состоянии (можно использовать FSM или временное хранилище)
#     # Для простоты сохраним в availability_states
#     state.selected_house_id = house_id
#     state.waiting_for_guest_name = True
#
#     # Запрашиваем имя гостя
#     await callback.message.edit_text(
#         f"📝 <b>Бронирование {house.name}</b>\n\n"
#         f"📅 Даты: {state.check_in.strftime('%d.%m.%Y')} - {state.check_out.strftime('%d.%m.%Y')}\n"
#         f"🌙 Ночей: {nights}\n\n"
#         f"Пожалуйста, введите <b>имя гостя</b>:",
#         parse_mode="HTML"
#     )
#     await callback.answer()

# @router.message(F.text)
# async def handle_guest_name_input(message: Message):
#     """Обработчик ввода имени гостя для бронирования"""
#     if message.from_user is None or message.text is None:
#         return
#
#     user_id = message.from_user.id
#     state = availability_states.get(user_id)
#
#     # Проверяем, ожидаем ли мы ввод имени гостя
#     if not state or not state.waiting_for_guest_name:
#         return  # Не наш случай, пропускаем
#
#     # Проверяем наличие всех необходимых данных
#     if not state.check_in or not state.check_out or not state.selected_house_id:
#         await message.answer("❌ Ошибка: данные бронирования потеряны. Попробуйте снова через /availability")
#         state.waiting_for_guest_name = False
#         return
#
#     guest_name = message.text.strip()
#
#     # Валидация имени
#     if len(guest_name) < 2:
#         await message.answer("❌ Имя слишком короткое. Пожалуйста, введите полное имя гостя:")
#         return
#
#     # Сбрасываем флаг ожидания
#     state.waiting_for_guest_name = False
#
#     # Показываем индикатор загрузки
#     loading_msg = await message.answer("⏳ Создаю бронирование...")
#
#     # Вычисляем количество ночей
#     nights = (state.check_out - state.check_in).days
#
#     # Получаем информацию о доме для расчета цены
#     from app.services.house_service import house_service
#     house = await house_service.get_house(state.selected_house_id)
#
#     if not house:
#         await loading_msg.edit_text("❌ Ошибка: домик не найден")
#         return
#
#     # Создаем бронирование
#     booking_data = {
#         'house_id': state.selected_house_id,
#         'guest_name': guest_name,
#         'check_in': state.check_in,
#         'check_out': state.check_out,
#         'guests_count': 1,  # По умолчанию, можно расширить позже
#         'total_price': 0,  # Можно добавить расчет цены позже
#     }
#
#     booking = await booking_service.create_booking(booking_data)
#
#     if not booking:
#         await loading_msg.edit_text("❌ Ошибка при создании бронирования. Попробуйте позже.")
#         return
#
#     # Успешное создание
#     from app.telegram.auth.admin import is_admin
#     back_callback = "admin:menu" if is_admin(user_id) else "guest:menu"
#
#     await loading_msg.edit_text(
#         f"✅ <b>Бронирование создано!</b>\n\n"
#         f"🏠 Домик: {house.name}\n"
#         f"👤 Гость: {guest_name}\n"
#         f"📅 Даты: {state.check_in.strftime('%d.%m.%Y')} - {state.check_out.strftime('%d.%m.%Y')}\n"
#         f"🌙 Ночей: {nights}\n"
#         f"🆔 ID брони: #{booking.id}\n\n"
#         f"Бронирование сохранено и синхронизируется с Google Таблицами.",
#         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text="🔙 В меню", callback_data=back_callback)]
#         ]),
#         parse_mode="HTML"
#     )
#
#     # Очищаем состояние
#     availability_states.pop(user_id, None)


@router.message(Command("broni"))
@router.message(F.text.lower().in_(["брони", "бронь", "заезды", "гости"]))
@router.callback_query(F.data == "bookings:menu")
async def show_bookings_menu(event: Message | CallbackQuery):
    """Главное меню броней"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔔 Заезды сегодня", callback_data="bookings:today"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Заезды на неделю", callback_data="bookings:week"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Все активные", callback_data="bookings:active"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Все брони (включая старые)", callback_data="bookings:all"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Обновить и открыть таблицу",
                    callback_data="bookings:sync_open",
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin:menu")],
        ]
    )

    text = "🏕 <b>Управление бронями</b>\n\nЧто хотите посмотреть?"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "bookings:today")
async def show_today_bookings(callback: CallbackQuery):
    today = date.today()
    await show_bookings_list(
        callback, start_date=today, end_date=today, title="Заезды сегодня"
    )


@router.callback_query(F.data == "bookings:week")
async def show_week_bookings(callback: CallbackQuery):
    today = date.today()
    week_end = today + timedelta(days=7)
    await show_bookings_list(
        callback, start_date=today, end_date=week_end, title="Заезды на неделю"
    )


@router.callback_query(F.data == "bookings:active")
async def show_active_bookings(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Booking)
            .options(joinedload(Booking.house))
            .where(
                Booking.status.in_(
                    [
                        BookingStatus.CONFIRMED,
                        BookingStatus.PAID,
                        BookingStatus.NEW,
                        BookingStatus.CHECKING_IN,
                        BookingStatus.CHECKED_IN,
                    ]
                ),
                Booking.check_out >= date.today(),
            )
            .order_by(Booking.check_in)
        )
        result = await session.execute(stmt)
        bookings = result.scalars().all()

    await send_bookings_response(callback, bookings, "Все активные брони")


@router.callback_query(F.data == "bookings:checked_in")
async def show_checked_in_bookings(callback: CallbackQuery):
    """Показать гостей, которые сейчас проживают"""
    today = date.today()
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Booking)
            .options(joinedload(Booking.house))
            .where(
                Booking.status == BookingStatus.CHECKED_IN,
                Booking.check_in <= today,
                Booking.check_out > today,
            )
            .order_by(Booking.house_id, Booking.check_in)
        )
        result = await session.execute(stmt)
        bookings = result.scalars().all()

    await send_bookings_response(callback, bookings, "🏠 Проживают сейчас")


@router.callback_query(F.data == "bookings:checking_in")
async def show_checking_in_bookings(callback: CallbackQuery):
    """Показать гостей с заездом сегодня"""
    today = date.today()
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Booking)
            .options(joinedload(Booking.house))
            .where(
                Booking.status == BookingStatus.CHECKING_IN, Booking.check_in == today
            )
            .order_by(Booking.house_id)
        )
        result = await session.execute(stmt)
        bookings = result.scalars().all()

    await send_bookings_response(callback, bookings, "🔔 Заезд сегодня")


@router.callback_query(F.data == "bookings:all")
async def show_all_bookings(callback: CallbackQuery):
    """Показать ВСЕ брони, включая старые и тестовые"""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Booking)
            .options(joinedload(Booking.house))
            .order_by(Booking.check_in.desc())
        )
        result = await session.execute(stmt)
        bookings = result.scalars().all()

    await send_bookings_response(callback, bookings, "Все брони (включая старые)")




async def show_bookings_list(
    callback: CallbackQuery, start_date: date, end_date: date, title: str
):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Booking)
            .options(joinedload(Booking.house))
            .where(Booking.check_in >= start_date, Booking.check_in <= end_date)
            .order_by(Booking.check_in)
        )
        result = await session.execute(stmt)
        bookings = result.scalars().all()

    await send_bookings_response(callback, bookings, title)


async def send_bookings_response(
    callback: CallbackQuery, bookings: list[Booking], title: str
):
    """Отправка списка броней с кнопками управления"""

    if not bookings:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад к бронированиям", callback_data="bookings:menu"
                    )
                ]
            ]
        )
        await callback.message.edit_text(
            f"<b>{title}</b>\n\nНет броней за этот период 🤷‍♂️", reply_markup=keyboard
        )
        await callback.answer()
        return

    # Формируем текст списка
    text = f"<b>{title} ({len(bookings)})</b>\n\n"

    status_emoji = {
        BookingStatus.NEW: "🆕",
        BookingStatus.CONFIRMED: "✅",
        BookingStatus.PAID: "💰",
        BookingStatus.CHECKING_IN: "🔔",
        BookingStatus.CHECKED_IN: "🏠",
        BookingStatus.CANCELLED: "❌",
        BookingStatus.COMPLETED: "🏁",
    }

    # Создаем кнопки для каждой брони (макс 10 на страницу для удобства)
    buttons = []
    current_row = []

    for b in bookings:
        # Определяем источник брони
        from app.models import BookingSource

        source_emoji = "🅰️" if b.source == BookingSource.AVITO else "🅣"

        text += (
            f"#{b.id} {status_emoji.get(b.status, '❓')} {source_emoji} "
            f"{b.check_in.strftime('%d.%m')}-{b.check_out.strftime('%d.%m')} | "
            f"{b.house.name} | {b.guest_name}\n"
        )

        # Добавляем кнопку с ID
        current_row.append(
            InlineKeyboardButton(text=f"#{b.id}", callback_data=f"booking:view:{b.id}")
        )

        if len(current_row) == 5:  # 5 кнопок в ряд
            buttons.append(current_row)
            current_row = []

    if current_row:
        buttons.append(current_row)

    # Кнопка назад
    buttons.append(
        [
            InlineKeyboardButton(
                text="🔙 Назад к меню броней", callback_data="bookings:menu"
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "bookings:sync_open")
async def sync_and_open_table(callback: CallbackQuery):
    """Синхронизация с Авито и открытие таблицы"""

    # Редактируем сообщение, показывая статус
    await callback.message.edit_text(
        "⏳ <b>Синхронизируем данные с Avito...</b>", parse_mode="HTML"
    )

    # 1. Синхронизация с Avito (получение новых броней)
    await sync_avito_job()

    # 1.5 Проверка и блокировка локальных броней в Avito
    await callback.message.edit_text(
        "🔍 <b>Проверяем брони в Avito...</b>", parse_mode="HTML"
    )
    from app.jobs.avito_sync_job import verify_local_bookings_in_avito

    # Парсим маппинг item_id:house_id
    item_house_mapping = {}
    for pair in settings.avito_item_ids.split(","):
        pair = pair.strip()
        if ":" in pair:
            item_id, house_id = pair.split(":")
            item_house_mapping[int(item_id)] = int(house_id)

    if item_house_mapping:
        await verify_local_bookings_in_avito(item_house_mapping)

    # 2. Обновление статуса
    await callback.message.edit_text(
        "⏳ <b>Обновляем Google Sheets...</b>", parse_mode="HTML"
    )

    # 3. Принудительная синхронизация таблицы
    # Используем to_thread т.к. sync_bookings_to_sheet синхронная, но вызываем через сервис для правильности
    from app.services.sheets_service import sheets_service
    import asyncio

    # Получаем актуальные брони для таблицы
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Booking)
            .options(joinedload(Booking.house))
            .order_by(Booking.check_in)
        )
        result = await session.execute(stmt)
        bookings = result.scalars().all()

    # Отправляем в GS
    try:
        await asyncio.to_thread(sheets_service.sync_bookings_to_sheet, bookings)
        status_text = "✅ <b>Синхронизация завершена!</b>\n\nДанные актуализированы."
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        # Логируем ошибку, но не отправляем юзеру страшный текст, если это не invalid_grant
        if "invalid_grant" in str(e):
            status_text = (
                "⚠️ <b>Ошибка доступа к Google Таблице!</b>\n\n"
                "Система не может обновить таблицу. Возможно, устарели ключи доступа или удален сервисный аккаунт.\n"
                "Синхронизация с Avito прошла успешно, но таблица не обновлена."
            )
        else:
            status_text = (
                f"⚠️ <b>Ошибка при обновлении таблицы!</b>\n\n"
                f"Синхронизация с Avito прошла, но таблицу обновить не удалось.\n"
                f"Детали ошибки: {str(e)}"
            )
        # Логируем в консоль для админа
        print(f"Sheets Sync Error: {error_details}")

    # 4. Финиш - даем ссылку
    sheet_link = f"https://docs.google.com/spreadsheets/d/{settings.google_sheets_spreadsheet_id}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Перейти в таблицу", url=sheet_link)],
            [
                InlineKeyboardButton(
                    text="🔙 К списку броней", callback_data="bookings:menu"
                )
            ],
        ]
    )

    await callback.message.edit_text(
        status_text, reply_markup=keyboard, parse_mode="HTML"
    )
    await callback.answer()
