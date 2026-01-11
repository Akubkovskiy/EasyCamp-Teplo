import logging
from typing import List, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.models import Booking
from app.services.notification_service import notification_service, NotificationRule

logger = logging.getLogger(__name__)


def format_welcome_message(bookings: List[Booking], recipient: Any) -> str:
    """Сообщение за 2 дня до заезда"""
    b = bookings[0]
    return (
        f"👋 <b>Здравствуйте, {recipient.name}!</b>\n\n"
        f"Напоминаем, что через 2 дня (<b>{b.check_in.strftime('%d.%m')}</b>) "
        f"мы ждем вас в гости в нашем домике <b>{b.house.name}</b>! 🏕\n\n"
        "⏰ Заезд запланирован после 14:00.\n"
        "📍 Координаты и инструкцию по заселению мы пришлем в день заезда.\n\n"
        "Если у вас остались вопросы, мы всегда на связи!"
    )

def format_checkin_message(bookings: List[Booking], recipient: Any) -> str:
    """Сообщение в день заезда"""
    b = bookings[0]
    return (
        f"🔑 <b>День заезда!</b>\n\n"
        f"Добро пожаловать в <b>{b.house.name}</b>.\n"
        "Код от кейбокса (ключа): <code>1234</code>\n"  # TODO: Динамический код
        "Пароль от Wi-Fi: <code>teplo_mountains</code>\n\n"
        "Желаем вам отличного отдыха! 🌲"
    )

def format_checkout_message(bookings: List[Booking], recipient: Any) -> str:
    """Сообщение в день выезда"""
    return (
        "😿 <b>День выезда</b>\n\n"
        "Надеемся, вам понравилось отдыхать у нас!\n"
        "Напоминаем, что выезд до 12:00.\n\n"
        "Будем рады видеть вас снова! 🤗"
    )


async def check_and_notify_guests():
    """Запуск проверки уведомлений для гостей"""
    logger.info("Checking guest notifications...")
    
    # 1. За 2 дня до заезда
    await notification_service.process_rule(NotificationRule(
        name="GuestWelcome",
        reference_field="check_in",
        days_offset=2,
        recipient_type="guest",
        message_func=format_welcome_message
    ))
    
    # 2. В день заезда (Сегодня, 0 смещение)
    await notification_service.process_rule(NotificationRule(
        name="GuestCheckIn",
        reference_field="check_in",
        days_offset=0,
        recipient_type="guest",
        message_func=format_checkin_message
    ))
    
    # 3. В день выезда (Сегодня, 0 смещение)
    await notification_service.process_rule(NotificationRule(
        name="GuestCheckOut",
        reference_field="check_out",
        days_offset=0,
        recipient_type="guest",
        message_func=format_checkout_message
    ))
