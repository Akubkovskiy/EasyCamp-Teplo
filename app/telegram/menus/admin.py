from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.core.config import settings


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Проверить доступность",
                    callback_data="admin:availability",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Домики",
                    callback_data="admin:houses",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🆕 Создать бронь",
                    callback_data="admin:new_booking",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Список броней",
                    callback_data="bookings:menu",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧹 Уборки",
                    callback_data="admin:cleaning",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data="admin:settings",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📞 Контакты",
                    callback_data="contacts",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌐 Открыть админку",
                    url=settings.admin_web_url,
                )
            ],
        ]
    )
