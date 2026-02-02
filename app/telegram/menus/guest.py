from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def guest_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню для авторизованного гостя"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Моя бронь", callback_data="guest:my_booking"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗺 Как добраться", callback_data="guest:directions"
                ),
                InlineKeyboardButton(text="ℹ️ Правила", callback_data="guest:rules"),
            ],
            [
                InlineKeyboardButton(
                    text="📞 Связь с админом", callback_data="guest:contact_admin"
                )
            ],
        ]
    )


def request_contact_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса контакта (Login)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Найти мою бронь (Поделиться телефоном)",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
