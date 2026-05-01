"""Cleaner-facing inline keyboards."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_cleaner_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Задачи сегодня", callback_data="cleaner:tasks:today")],
            [
                InlineKeyboardButton(text="📅 Брони на неделю", callback_data="cleaner:schedule:week_full"),
                InlineKeyboardButton(text="📆 Брони на месяц", callback_data="cleaner:schedule:month"),
            ],
            [
                InlineKeyboardButton(text="💰 Мои выплаты", callback_data="cleaner:pay"),
                InlineKeyboardButton(text="🧾 Расходники", callback_data="cleaner:expense:new"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="cleaner:settings"),
                InlineKeyboardButton(text="❓ Помощь", callback_data="cleaner:help"),
            ],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="cleaner:menu")],
        ]
    )
