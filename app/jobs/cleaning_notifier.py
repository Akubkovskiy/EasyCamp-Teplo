import logging
from datetime import date, timedelta
from typing import List, Any

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.models import Booking
from app.services.notification_service import notification_service, NotificationRule

logger = logging.getLogger(__name__)


def format_cleaning_message(bookings: List[Booking], recipient: Any) -> str:
    """Формирует сообщение для уборщицы"""
    target_date = bookings[0].check_out # Все брони на одну дату
    msg_header = f"🧹 <b>План уборки на ЗАВТРА ({target_date.strftime('%d.%m')})</b>\n\n"
    msg_body = ""
    
    for b in bookings:
        msg_body += (
            f"🏠 <b>{b.house.name}</b>\n"
            f"👤 Гости: {b.guests_count} чел\n"
            f"📞 {b.guest_phone}\n\n"
        )
        
    msg_footer = "⚠️ <b>Пожалуйста, подтвердите выход на смену!</b>"
    return msg_header + msg_body + msg_footer


def format_cleaning_keyboard(bookings: List[Booking], recipient: Any) -> InlineKeyboardMarkup:
    """Формирует клавиатуру подтверждения"""
    target_date = bookings[0].check_out
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтверждаю", callback_data=f"cleaner:confirm:{target_date}"),
            InlineKeyboardButton(text="❌ Не смогу", callback_data=f"cleaner:decline:{target_date}")
        ]
    ])


async def check_and_notify_cleaners():
    """Проверяет выезды на ЗАВТРА и уведомляет уборщиц через Service"""
    
    rule = NotificationRule(
        name="CleanerTomorrowCheckout",
        reference_field="check_out",
        days_offset=1, # Завтра
        recipient_type="cleaner",
        message_func=format_cleaning_message,
        keyboard_func=format_cleaning_keyboard
    )
    
    await notification_service.process_rule(rule)
