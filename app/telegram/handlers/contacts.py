"""Обработчики контактной информации."""

from app.core.messages import messages
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

router = Router()


def _contacts_keyboard(back_callback: str = "admin:menu") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="💬 Написать в Telegram", url=messages.CONTACT_ADMIN_URL)],
    ]
    if messages.SITE_URL:
        rows.append([InlineKeyboardButton(text="🌐 Наш сайт", url=messages.SITE_URL)])
    if messages.YANDEX_REVIEWS_URL:
        rows.append([InlineKeyboardButton(text="⭐ Отзывы на Яндекс.Картах", url=messages.YANDEX_REVIEWS_URL)])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery):
    await callback.message.edit_text(
        messages.CONTACTS_INFO,
        reply_markup=_contacts_keyboard("admin:menu"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "guest:contacts")
async def show_guest_contacts(callback: CallbackQuery):
    await callback.message.edit_text(
        messages.CONTACTS_INFO,
        reply_markup=_contacts_keyboard("guest:showcase:menu"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(F.text.lower().in_(["контакты", "связаться", "телефон", "помощь"]))
async def show_contacts_message(message: Message):
    rows = [
        [InlineKeyboardButton(text="💬 Написать в Telegram", url=messages.CONTACT_ADMIN_URL)],
    ]
    if messages.SITE_URL:
        rows.append([InlineKeyboardButton(text="🌐 Наш сайт", url=messages.SITE_URL)])
    if messages.YANDEX_REVIEWS_URL:
        rows.append([InlineKeyboardButton(text="⭐ Отзывы на Яндекс.Картах", url=messages.YANDEX_REVIEWS_URL)])
    await message.answer(
        messages.CONTACTS_INFO,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode="HTML",
    )
