"""
Регистрация Bot Menu Commands (кнопка Menu слева от поля ввода).

Разные наборы команд для разных ролей через BotCommandScope.
"""

import logging

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

logger = logging.getLogger(__name__)

# --- Команды для гостей (default scope — видят все) ---
GUEST_COMMANDS = [
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="about", description="О базе отдыха"),
    BotCommand(command="dates", description="Проверить свободные даты"),
    BotCommand(command="location", description="Где мы находимся"),
    BotCommand(command="contact", description="Связаться с нами"),
    BotCommand(command="login", description="Авторизоваться по брони"),
    BotCommand(command="booking", description="Моя бронь"),
]


async def setup_commands(bot: Bot) -> None:
    """Устанавливает команды бота для всех scope."""

    # Default (все пользователи = гости)
    await bot.set_my_commands(GUEST_COMMANDS, scope=BotCommandScopeDefault())
    logger.info("Bot menu commands set for guests (default scope)")
