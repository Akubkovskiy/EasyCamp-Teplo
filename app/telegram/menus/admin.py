from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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
                    text="🏠 Календарь домов",
                    callback_data="admin:houses",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Бронирования",
                    callback_data="bookings:menu",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data="admin:settings",
                )
            ],
        ]
    )
