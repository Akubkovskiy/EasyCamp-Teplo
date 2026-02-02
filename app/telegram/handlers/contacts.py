"""
Обработчики для контактной информации
"""

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


router = Router()


@router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery):
    """Показать контактную информацию"""

    # Формируем контактную информацию
    text = (
        "📞 <b>Контакты администрации</b>\n\n"
        "🏕 <b>База отдыха Teplo · Архыз</b>\n\n"
        "📱 Телефон: +7 (925) 127-97-22\n"
        "💬 Telegram: @Alexey_kubkovskiy\n"
        "📧 Email: teploarkhyz@gmail.com\n\n"
        "🕐 Режим работы: Круглосуточно\n"
        "📍 Адрес: Карачаево-Черкесия, Архыз\n\n"
        "Мы всегда рады помочь! 🤗"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать в Telegram", url="https://t.me/Alexey_kubkovskiy"
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin:menu")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.message(F.text.lower().in_(["контакты", "связаться", "телефон", "помощь"]))
async def show_contacts_message(message: Message):
    """Показать контакты по текстовой команде"""

    text = (
        "📞 <b>Контакты администрации</b>\n\n"
        "🏕 <b>База отдыха Teplo · Архыз</b>\n\n"
        "📱 Телефон: +7 (925) 127-97-22\n"
        "💬 Telegram: @Alexey_kubkovskiy\n"
        "📧 Email: teploarkhyz@gmail.com\n\n"
        "🕐 Режим работы: Круглосуточно\n"
        "📍 Адрес: Карачаево-Черкесия, Архыз\n\n"
        "Мы всегда рады помочь! 🤗"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать в Telegram", url="https://t.me/Alexey_kubkovskiy"
                )
            ],
        ]
    )

    await message.answer(text, reply_markup=keyboard)
