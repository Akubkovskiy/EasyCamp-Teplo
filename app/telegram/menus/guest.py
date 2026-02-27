from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def guest_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню для АВТОРИЗОВАННОГО гостя"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔑 Инструкция по заселению", callback_data="guest:instruction")],
            [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="guest:contact_admin")],
            [InlineKeyboardButton(text="🛣 Как добраться", callback_data="guest:directions")],
            [InlineKeyboardButton(text="🏠 Моя бронь", callback_data="guest:my_booking")],
            [InlineKeyboardButton(text="💳 Оплата", callback_data="guest:pay")],
            [InlineKeyboardButton(text="📶 Wi‑Fi", callback_data="guest:wifi")],
            [InlineKeyboardButton(text="ℹ️ Правила", callback_data="guest:rules")],
            [InlineKeyboardButton(text="🤝 Партнёры", callback_data="guest:partners")],
        ]
    )


def guest_showcase_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура витрины для НЕавторизованного гостя"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏕 О базе", callback_data="guest:showcase:about")],
            [InlineKeyboardButton(text="🏠 Домики и фото", callback_data="guest:showcase:houses")],
            [InlineKeyboardButton(text="📅 Проверить даты и забронировать", callback_data="guest:availability")],
            [InlineKeyboardButton(text="❓ Популярные вопросы", callback_data="guest:showcase:faq")],
            [InlineKeyboardButton(text="📍 Где мы находимся", callback_data="guest:showcase:location")],
            [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="guest:contact_admin")],
            [InlineKeyboardButton(text="🔐 Авторизоваться", callback_data="guest:auth")],
        ]
    )


def request_contact_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса контакта (Login)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Поделиться моим телефоном",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
