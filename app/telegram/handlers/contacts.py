"""
Обработчики для контактной информации
"""

from app.core.messages import messages
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
    text = messages.CONTACTS_INFO

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать в Telegram", url=messages.CONTACT_ADMIN_URL
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

    text = messages.CONTACTS_INFO

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать в Telegram", url=messages.CONTACT_ADMIN_URL
                )
            ],
        ]
    )

    await message.answer(text, reply_markup=keyboard)
