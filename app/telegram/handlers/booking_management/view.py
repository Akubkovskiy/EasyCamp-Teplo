"""
Обработчики для ПРОСМОТРА и ОТМЕНЫ бронирований
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from app.services.booking_service import booking_service
from app.models import BookingStatus

router = Router()

@router.callback_query(F.data.startswith("booking:view:"))
async def view_booking_details(callback: CallbackQuery):
    """Просмотр деталей брони"""
    booking_id = int(callback.data.split(":")[2])
    await render_booking_card(callback, booking_id)

async def render_booking_card(event: CallbackQuery | Message, booking_id: int):
    """Отрисовка карточки брони (общая логика)"""
    booking = await booking_service.get_booking(booking_id)
    
    if not booking:
        if isinstance(event, CallbackQuery):
            await event.answer("❌ Бронь не найдена", show_alert=True)
        else:
            await event.answer("❌ Бронь не найдена")
        return
        
    status_emoji = {
        BookingStatus.NEW: "🆕",
        BookingStatus.CONFIRMED: "✅",
        BookingStatus.PAID: "💰",
        BookingStatus.CANCELLED: "❌",
        BookingStatus.COMPLETED: "🏁",
    }
    
    # Расчет суток
    nights = (booking.check_out - booking.check_in).days
    
    # Финансы
    advance = booking.advance_amount or 0
    remaining = booking.total_price - advance
    
    # Русские названия статусов
    status_names = {
        BookingStatus.NEW: "Ожидает",
        BookingStatus.CONFIRMED: "Подтверждено",
        BookingStatus.PAID: "Оплачено",
        BookingStatus.CANCELLED: "Отменено",
        BookingStatus.COMPLETED: "Завершено",
    }
    
    status_display = status_names.get(booking.status, booking.status.value)

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
        f"📊 Статус: {status_emoji.get(booking.status, '❓')} <b>{status_display}</b>\n"
        f"🔗 Источник: {booking.source.value}\n"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Изменить", callback_data=f"booking:edit:{booking.id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"booking:cancel:{booking.id}"),
        ],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="bookings:menu")]
    ])
    
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
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, отменить", callback_data=f"booking:cancel_confirm:{booking_id}"),
            InlineKeyboardButton(text="❌ Нет, оставить", callback_data=f"booking:view:{booking_id}"),
        ]
    ])
    
    await callback.message.edit_text(
        f"⚠️ <b>Вы уверены, что хотите отменить бронь #{booking_id}?</b>\n\n"
        "Это действие изменит статус на CANCELLED и обновит Google Sheets.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("booking:cancel_confirm:"))
async def execute_cancel(callback: CallbackQuery):
    """Выполнение отмены"""
    booking_id = int(callback.data.split(":")[2])
    
    # Сразу даем обратную связь
    await callback.message.edit_text("⏳ Отменяем бронь...", reply_markup=None)
    
    success = await booking_service.cancel_booking(booking_id)
    
    if success:
        await callback.message.edit_text(
            f"✅ <b>Бронь #{booking_id} отменена</b>\n\nСтатус обновлен.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку броней", callback_data="bookings:menu")]
            ]),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"❌ Ошибка при отмене брони #{booking_id}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку броней", callback_data="bookings:menu")]
            ])
        )
    await callback.answer()
