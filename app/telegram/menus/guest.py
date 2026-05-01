from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from app.core.config import settings


def guest_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню для АВТОРИЗОВАННОГО гостя."""
    rows = [
        [InlineKeyboardButton(text="🏠 Моя бронь", callback_data="guest:my_booking")],
        [InlineKeyboardButton(text="💳 Оплата", callback_data="guest:pay")],
        [InlineKeyboardButton(text="🔑 Инструкция по заселению", callback_data="guest:instruction")],
        [InlineKeyboardButton(text="📶 Wi‑Fi", callback_data="guest:wifi")],
        [InlineKeyboardButton(text="🛣 Как добраться", callback_data="guest:directions")],
        [InlineKeyboardButton(text="ℹ️ Правила проживания", callback_data="guest:rules")],
        [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="guest:contact_admin")],
    ]

    if settings.guest_feature_partners:
        rows.append([InlineKeyboardButton(text="🤝 Партнёры", callback_data="guest:partners")])

    if settings.yandex_reviews_url:
        rows.append([InlineKeyboardButton(text="⭐ Оставить отзыв", url=settings.yandex_reviews_url)])

    rows.append([InlineKeyboardButton(text="🚪 Выйти", callback_data="guest:logout")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def guest_showcase_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура витрины для НЕавторизованного гостя."""
    rows = [
        [InlineKeyboardButton(text="📅 Проверить даты и забронировать", callback_data="guest:availability")],
    ]

    if settings.guest_feature_showcase_houses:
        rows.append([InlineKeyboardButton(text="🏠 Наши домики", callback_data="guest:showcase:houses")])

    rows.append([InlineKeyboardButton(text="🏕 О базе", callback_data="guest:showcase:about")])
    rows.append([InlineKeyboardButton(text="📍 Как добраться", callback_data="guest:showcase:location")])

    if settings.guest_feature_faq:
        rows.append([InlineKeyboardButton(text="❓ Вопросы и ответы", callback_data="guest:showcase:faq")])

    rows.append([InlineKeyboardButton(text="📞 Связаться с нами", callback_data="guest:contact_admin")])

    if settings.yandex_reviews_url:
        rows.append([InlineKeyboardButton(text="⭐ Отзывы", url=settings.yandex_reviews_url)])

    rows.append([InlineKeyboardButton(text="🔐 Авторизоваться", callback_data="guest:auth")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


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
