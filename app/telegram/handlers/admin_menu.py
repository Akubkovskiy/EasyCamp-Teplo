import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

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
        await callback.message.edit_text(
            "🏕 <b>Teplo · Архыз</b>\n\nАдминистративная панель",
            reply_markup=admin_menu_keyboard(),
        )
    await callback.answer()


@router.callback_query(lambda c: c.data == "admin:houses")
async def show_houses_calendar(callback: CallbackQuery):
    """Заглушка для календаря домов"""
    logger.info("Houses calendar requested")
    
    if callback.message:
        await callback.message.edit_text(
            "🏠 <b>Календарь домов</b>\n\n"
            "⚠️ Функция в разработке\n\n"
            "Здесь будет отображаться:\n"
            "• Шахматка занятости по всем домикам\n"
            "• Визуальный календарь на месяц\n"
            "• Быстрый просмотр свободных дат",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin:menu")]
            ])
        )
    await callback.answer()


@router.callback_query(lambda c: c.data == "admin:settings")
async def show_settings(callback: CallbackQuery):
    """Заглушка для настроек"""
    logger.info("Settings requested")
    
    if callback.message:
        await callback.message.edit_text(
            "⚙️ <b>Настройки</b>\n\n"
            "⚠️ Функция в разработке\n\n"
            "Здесь будут доступны:\n"
            "• Управление домиками\n"
            "• Настройка уведомлений\n"
            "• Интеграции (Avito, другие платформы)\n"
            "• Управление персоналом",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin:menu")]
            ])
        )
    await callback.answer()
