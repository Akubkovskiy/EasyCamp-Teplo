"""
Обработчики для ПРОСМОТРА и ОТМЕНЫ бронирований
"""

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from app.database import AsyncSessionLocal
from app.services.booking_service import BookingService
from app.models import BookingSource, BookingStatus
from app.telegram.ui.booking_format import BOOKING_SOURCE_EMOJI, BOOKING_STATUS_EMOJI, BOOKING_STATUS_NAMES

router = Router()


def _back_to_bookings_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку броней", callback_data="bookings:menu")],
    ])


@router.callback_query(F.data.startswith("booking:view:"))
async def view_booking_details(callback: CallbackQuery):
    """Просмотр деталей брони"""
    booking_id = int(callback.data.split(":")[2])
    await render_booking_card(callback, booking_id)


async def render_booking_card(event: CallbackQuery | Message, booking_id: int):
    """Отрисовка карточки брони (общая логика)"""
    async with AsyncSessionLocal() as db:
        booking = await BookingService.get_booking(db, booking_id)

    if not booking:
        if isinstance(event, CallbackQuery):
            await event.answer("❌ Бронь не найдена", show_alert=True)
        else:
            await event.answer("❌ Бронь не найдена")
        return

    # Расчет суток
    nights = (booking.check_out - booking.check_in).days

    # Финансы
    advance = booking.advance_amount or 0
    remaining = booking.total_price - advance

    status_display = BOOKING_STATUS_NAMES.get(booking.status, booking.status.value)

    text = (
        f"📋 <b>Бронирование #{booking.id}</b>\n\n"
        f"🏠 Домик: <b>{booking.house.name}</b>\n"
        f"📅 Даты: <code>{booking.check_in.strftime('%d.%m.%Y')} - {booking.check_out.strftime('%d.%m.%Y')}</code> ({nights} сут.)\n"
        f"👤 Гость: <b>{booking.guest_name}</b>\n"
        f"📞 Телефон: <code>{booking.guest_phone}</code>\n"
        f"👥 Гостей: {booking.guests_count}\n"
        f"──────────────────\n"
        f"💰 <b>Итого: {booking.total_price:,.0f} ₽</b>\n"
        f"💳 Аванс: {advance:,.0f} ₽\n"
        f"💵 Остаток: {remaining:,.0f} ₽\n"
        f"──────────────────\n"
        f"📊 Статус: {BOOKING_STATUS_EMOJI.get(booking.status, '❓')} <b>{status_display}</b>\n"
        f"{BOOKING_SOURCE_EMOJI.get(booking.source, '❓')} Источник: {booking.source.value}\n"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить", callback_data=f"booking:edit:{booking.id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"booking:cancel:{booking.id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить", callback_data=f"booking:delete:{booking.id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад к списку", callback_data="bookings:menu"
                )
            ],
        ]
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()
    else:
        # Если это Message, то просто отправляем новое сообщение
        await event.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("booking:cancel:"))
async def request_cancel_confirmation(callback: CallbackQuery):
    """Запрос подтверждения отмены"""
    booking_id = int(callback.data.split(":")[2])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, отменить",
                    callback_data=f"booking:cancel_confirm:{booking_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Нет, оставить", callback_data=f"booking:view:{booking_id}"
                ),
            ]
        ]
    )

    await callback.message.edit_text(
        f"⚠️ <b>Вы уверены, что хотите отменить бронь #{booking_id}?</b>\n\n"
        "Это действие изменит статус на CANCELLED и обновит Google Sheets.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("booking:cancel_confirm:"))
async def execute_cancel(callback: CallbackQuery):
    """Выполнение отмены"""
    booking_id = int(callback.data.split(":")[2])

    # Сразу даем обратную связь
    await callback.message.edit_text("⏳ Отменяем бронь...", reply_markup=None)

    async with AsyncSessionLocal() as db:
        success = await BookingService.cancel_booking(db, booking_id)

    if success:
        await callback.message.edit_text(
            f"✅ <b>Бронь #{booking_id} отменена</b>\n\nСтатус обновлен.",
            reply_markup=_back_to_bookings_kb(),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            f"❌ Ошибка при отмене брони #{booking_id}",
            reply_markup=_back_to_bookings_kb(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("booking:delete:"))
async def request_delete_confirmation(callback: CallbackQuery):
    """Запрос подтверждения удаления"""
    booking_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as db:
        booking = await BookingService.get_booking(db, booking_id)

    if not booking:
        await callback.answer("❌ Бронь не найдена", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Да, удалить навсегда",
                callback_data=f"booking:delete_confirm:{booking_id}",
            )],
            [InlineKeyboardButton(
                text="❌ Нет, вернуться", callback_data=f"booking:view:{booking_id}"
            )],
        ]
    )

    await callback.message.edit_text(
        f"⚠️ <b>ВНИМАНИЕ! Удаление брони #{booking_id}</b>\n\n"
        f"👤 Гость: <b>{booking.guest_name}</b>\n"
        f"📅 Даты: {booking.check_in.strftime('%d.%m.%Y')} - {booking.check_out.strftime('%d.%m.%Y')}\n"
        f"🏠 Дом: {booking.house.name}\n\n"
        f"🗑️ <b>Это действие НЕОБРАТИМО!</b>\n"
        f"Бронь будет полностью удалена из базы данных.\n\nВы уверены?",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("booking:delete_confirm:"))
async def execute_delete(callback: CallbackQuery):
    """Выполнение удаления"""
    booking_id = int(callback.data.split(":")[2])

    await callback.message.edit_text("⏳ Удаляем бронь из базы данных...", reply_markup=None)

    async with AsyncSessionLocal() as db:
        success = await BookingService.delete_booking(db, booking_id)

    if success:
        await callback.message.edit_text(
            f"✅ <b>Бронь #{booking_id} удалена</b>\n\n"
            f"Запись полностью удалена из базы данных.\n"
            f"Google Sheets обновляется в фоновом режиме.",
            reply_markup=_back_to_bookings_kb(),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            f"❌ Ошибка при удалении брони #{booking_id}",
            reply_markup=_back_to_bookings_kb(),
        )
    await callback.answer()
