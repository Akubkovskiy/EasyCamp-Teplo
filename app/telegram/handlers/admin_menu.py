import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from app.telegram.auth.admin import is_admin
from app.telegram.menus.admin import admin_menu_keyboard


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

    if not is_admin(message.from_user.id):
        logger.warning("Access denied for user_id=%s", message.from_user.id)
        await message.answer("Бот находится в разработке.")
        return

    await message.answer(
        "🏕 <b>Teplo · Архыз</b>\n\nАдминистративная панель",
        reply_markup=admin_menu_keyboard(),
    )


@router.callback_query(lambda c: c.data == "admin:menu")
async def back_to_menu(callback: CallbackQuery):
    logger.info("Back to admin menu")

    if callback.message:
        await callback.message.answer(
            "🏕 <b>Teplo · Архыз</b>\n\nАдминистративная панель",
            reply_markup=admin_menu_keyboard(),
        )
