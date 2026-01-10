"""
Обработчики настроек бота
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import os

from app.core.config import settings

router = Router()


@router.callback_query(F.data == "admin:settings")
@router.message(F.text == "⚙️ Настройки")
@router.message(Command("settings"))
async def show_settings(event):
    """Показать настройки"""
    
    # Определяем тип события
    if isinstance(event, CallbackQuery):
        message = event.message
        await event.answer()
    else:
        message = event
    
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Автосинхронизация", callback_data="settings_sync")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")],
    ])
    
    await message.answer(
        "⚙️ <b>Настройки</b>\n\n"
        "Выберите раздел:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "settings_sync")
async def sync_settings(callback: CallbackQuery):
    """Настройки синхронизации"""
    
    avito_status = "✅ Включено" if settings.avito_sync_interval_minutes > 0 else "❌ Выключено"
    sheets_status = "✅ Включено" if settings.sheets_sync_interval_minutes > 0 else "❌ Выключено"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"Avito: {settings.avito_sync_interval_minutes} мин {avito_status}",
            callback_data="edit_avito_interval"
        )],
        [InlineKeyboardButton(
            text=f"Sheets: {settings.sheets_sync_interval_minutes} мин {sheets_status}",
            callback_data="edit_sheets_interval"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")],
    ])
    
    await callback.message.edit_text(
        "🔄 <b>Настройки автосинхронизации</b>\n\n"
        f"<b>Avito синхронизация:</b> {avito_status}\n"
        f"Интервал: {settings.avito_sync_interval_minutes} минут\n\n"
        f"<b>Google Sheets синхронизация:</b> {sheets_status}\n"
        f"Интервал: {settings.sheets_sync_interval_minutes} минут\n\n"
        "<i>💡 Установите 0 чтобы отключить</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "edit_avito_interval")
async def edit_avito_interval(callback: CallbackQuery):
    """Изменить интервал Avito"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="0 (выкл)", callback_data="set_avito_0"),
            InlineKeyboardButton(text="15 мин", callback_data="set_avito_15"),
        ],
        [
            InlineKeyboardButton(text="30 мин", callback_data="set_avito_30"),
            InlineKeyboardButton(text="60 мин", callback_data="set_avito_60"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="settings_sync")],
    ])
    
    await callback.message.edit_text(
        "🔄 <b>Интервал синхронизации Avito</b>\n\n"
        f"Текущий: {settings.avito_sync_interval_minutes} минут\n\n"
        "Выберите новый интервал:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "edit_sheets_interval")
async def edit_sheets_interval(callback: CallbackQuery):
    """Изменить интервал Sheets"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="0 (выкл)", callback_data="set_sheets_0"),
            InlineKeyboardButton(text="5 мин", callback_data="set_sheets_5"),
        ],
        [
            InlineKeyboardButton(text="10 мин", callback_data="set_sheets_10"),
            InlineKeyboardButton(text="30 мин", callback_data="set_sheets_30"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="settings_sync")],
    ])
    
    await callback.message.edit_text(
        "📊 <b>Интервал синхронизации Google Sheets</b>\n\n"
        f"Текущий: {settings.sheets_sync_interval_minutes} минут\n\n"
        "Выберите новый интервал:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_avito_"))
async def set_avito_interval(callback: CallbackQuery):
    """Установить интервал Avito"""
    
    interval = int(callback.data.split("_")[2])
    
    # Обновляем .env файл
    update_env_variable("AVITO_SYNC_INTERVAL_MINUTES", str(interval))
    
    # Обновляем настройки в памяти
    settings.avito_sync_interval_minutes = interval
    
    # Перезапускаем планировщик
    from app.services.scheduler_service import scheduler_service
    scheduler_service.shutdown()
    scheduler_service.start()
    
    status = "выключена" if interval == 0 else f"установлена на {interval} минут"
    
    await callback.answer(f"✅ Avito синхронизация {status}", show_alert=True)
    await sync_settings(callback)


@router.callback_query(F.data.startswith("set_sheets_"))
async def set_sheets_interval(callback: CallbackQuery):
    """Установить интервал Sheets"""
    
    interval = int(callback.data.split("_")[2])
    
    # Обновляем .env файл
    update_env_variable("SHEETS_SYNC_INTERVAL_MINUTES", str(interval))
    
    # Обновляем настройки в памяти
    settings.sheets_sync_interval_minutes = interval
    
    # Перезапускаем планировщик
    from app.services.scheduler_service import scheduler_service
    scheduler_service.shutdown()
    scheduler_service.start()
    
    status = "выключена" if interval == 0 else f"установлена на {interval} минут"
    
    await callback.answer(f"✅ Sheets синхронизация {status}", show_alert=True)
    await sync_settings(callback)


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    """Вернуться к настройкам"""
    await show_settings(callback)


@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    """Вернуться в админ меню"""
    from app.telegram.menus.admin import admin_menu_keyboard
    
    await callback.message.edit_text(
        "🏕 <b>Teplo · Архыз</b>\n\nАдминистративная панель",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


def update_env_variable(key: str, value: str):
    """Обновить переменную в .env файле"""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        return
    
    # Читаем файл
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Обновляем нужную строку
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            updated = True
            break
    
    # Если не нашли - добавляем
    if not updated:
        lines.append(f"{key}={value}\n")
    
    # Записываем обратно
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
