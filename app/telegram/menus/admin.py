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
        ]
    )
