import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
)

from app.telegram.auth.admin import is_admin
from app.telegram.menus.admin import admin_menu_keyboard
from app.telegram.menus.guest import guest_menu_keyboard
from app.core.messages import messages


router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def start_handler(message: Message):
    if not message.from_user:
        return

    logger.info(
        "Received /start from user_id=%s username=%s",
        message.from_user.id,
        message.from_user.username,
    )

    # 1. Сначала проверяем админа
    if is_admin(message.from_user.id):
        await message.answer(
            messages.ADMIN_PANEL_TITLE,
            reply_markup=admin_menu_keyboard(),
        )
        return

    # 2. Проверяем уборщицу
    from app.telegram.auth.admin import is_cleaner

    if is_cleaner(message.from_user.id):
        from app.telegram.handlers.cleaner import show_cleaner_menu

        await show_cleaner_menu(message, message.from_user.id)
        return

    # 3. Иначе - гость (авторизованный или нет)
    from app.telegram.handlers.guest import show_guest_menu

    await show_guest_menu(message)


@router.callback_query(lambda c: c.data == "admin:menu")
async def back_to_menu(callback: CallbackQuery):
    logger.info("Back to admin menu")

    if callback.message:
        await callback.message.edit_text(
            messages.ADMIN_PANEL_TITLE,
            reply_markup=admin_menu_keyboard(),
        )
    await callback.answer()


@router.callback_query(lambda c: c.data == "guest:menu")
async def back_to_guest_menu(callback: CallbackQuery):
    logger.info("Back to guest menu")

    if callback.message:
        await callback.message.edit_text(
            messages.GUEST_MENU_TITLE,
            reply_markup=guest_menu_keyboard(),
        )
    await callback.answer()


# Обработчик admin:houses теперь в handlers/houses.py
