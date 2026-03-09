"""
Обработчики настроек бота
"""

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
import os

from app.core.config import settings
from app.core.messages import messages

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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Автосинхронизация", callback_data="settings_sync"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Период бронирования",
                    callback_data="settings_booking_window",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏰ Время уведомлений", callback_data="settings_cleaning_time"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Пользователи", callback_data="settings_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Редактор контента", callback_data="admin:settings:content"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Ценообразование", callback_data="settings_pricing"
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")],
        ]
    )

    await message.answer(
        "⚙️ <b>Настройки</b>\n\nВыберите раздел:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "settings_sync")
async def sync_settings(callback: CallbackQuery):
    """Настройки синхронизации"""

    avito_status = (
        "✅ Включено" if settings.avito_sync_interval_minutes > 0 else "❌ Выключено"
    )
    sheets_status = (
        "✅ Включено" if settings.sheets_sync_interval_minutes > 0 else "❌ Выключено"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Avito: {settings.avito_sync_interval_minutes} мин {avito_status}",
                    callback_data="edit_avito_interval",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Sheets: {settings.sheets_sync_interval_minutes} мин {sheets_status}",
                    callback_data="edit_sheets_interval",
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")],
        ]
    )

    await callback.message.edit_text(
        "🔄 <b>Настройки автосинхронизации</b>\n\n"
        f"<b>Avito синхронизация:</b> {avito_status}\n"
        f"Интервал: {settings.avito_sync_interval_minutes} минут\n\n"
        f"<b>Google Sheets синхронизация:</b> {sheets_status}\n"
        f"Интервал: {settings.sheets_sync_interval_minutes} минут\n\n"
        "<i>💡 Установите 0 чтобы отключить</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "settings_booking_window")
async def booking_window_settings(callback: CallbackQuery):
    """Настройки периода бронирования"""

    days = settings.booking_window_days
    months = days // 30

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📝 Изменить период ({days} дн.)",
                    callback_data="edit_booking_window",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Применить сейчас ко всем домам",
                    callback_data="apply_booking_window",
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")],
        ]
    )

    await callback.message.edit_text(
        "📅 <b>Период бронирования</b>\n\n"
        f"<b>Текущий период:</b> {days} дней (~{months} месяцев)\n\n"
        "<i>💡 Определяет, на сколько дней вперед открыты брони в Avito.\n"
        "Изменения применяются автоматически при создании/отмене брони.</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "edit_booking_window")
async def edit_booking_window(callback: CallbackQuery):
    """Изменить период бронирования"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="3 мес (90)", callback_data="set_window_90"),
                InlineKeyboardButton(
                    text="6 мес (180)", callback_data="set_window_180"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="9 мес (270)", callback_data="set_window_270"
                ),
                InlineKeyboardButton(
                    text="1 год (365)", callback_data="set_window_365"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад", callback_data="settings_booking_window"
                )
            ],
        ]
    )

    await callback.message.edit_text(
        "📅 <b>Период бронирования</b>\n\n"
        f"Текущий: {settings.booking_window_days} дней\n\n"
        "Выберите новый период:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_window_"))
async def set_booking_window(callback: CallbackQuery):
    """Установить период бронирования"""

    days = int(callback.data.split("_")[2])

    # Обновляем .env файл
    update_env_variable("BOOKING_WINDOW_DAYS", str(days))

    # Обновляем настройки в памяти
    settings.booking_window_days = days

    months = days // 30
    await callback.answer(
        f"✅ Период установлен: {days} дней (~{months} мес.)", show_alert=True
    )
    await booking_window_settings(callback)


@router.callback_query(F.data == "apply_booking_window")
async def apply_booking_window(callback: CallbackQuery):
    """Применить период бронирования ко всем домам"""

    await callback.answer("🔄 Обновляю календари...", show_alert=False)

    # Получаем маппинг домов
    from app.core.config import settings
    from app.services.avito_api_service import avito_api_service
    import asyncio

    item_house_mapping = {}
    for pair in settings.avito_item_ids.split(","):
        if ":" in pair:
            item_id, house_id = pair.strip().split(":")
            item_house_mapping[int(item_id)] = int(house_id)

    success_count = 0
    error_count = 0

    # Обновляем календарь для каждого дома
    for item_id, house_id in item_house_mapping.items():
        try:
            # Вызываем метод обновления календаря
            result = await asyncio.to_thread(
                avito_api_service.update_calendar_intervals, item_id
            )
            if result:
                success_count += 1
            else:
                error_count += 1
        except Exception:
            error_count += 1

    # Показываем результат
    result_text = ""
    if error_count == 0:
        result_text = f"✅ Календари обновлены!\n\nОбработано домов: {success_count}"
    else:
        result_text = (
            f"⚠️ Календари частично обновлены\n\n"
            f"Успешно: {success_count}\n"
            f"Ошибок: {error_count}"
        )

    # Используем answer вместо edit, чтобы избежать ошибки "message not modified"
    await callback.answer(result_text, show_alert=True)

    # Обновляем меню настроек
    days = settings.booking_window_days
    months = days // 30

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📝 Изменить период ({days} дн.)",
                    callback_data="edit_booking_window",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Применить сейчас ко всем домам",
                    callback_data="apply_booking_window",
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")],
        ]
    )

    await callback.message.edit_text(
        "📅 <b>Период бронирования</b>\n\n"
        f"<b>Текущий период:</b> {days} дней (~{months} месяцев)\n\n"
        "<i>💡 Определяет, на сколько дней вперед открыты брони в Avito.\n"
        "Изменения применяются автоматически при создании/отмене брони.</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "edit_avito_interval")
async def edit_avito_interval(callback: CallbackQuery):
    """Изменить интервал Avito"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="0 (выкл)", callback_data="set_avito_0"),
                InlineKeyboardButton(text="15 мин", callback_data="set_avito_15"),
            ],
            [
                InlineKeyboardButton(text="30 мин", callback_data="set_avito_30"),
                InlineKeyboardButton(text="60 мин", callback_data="set_avito_60"),
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="settings_sync")],
        ]
    )

    await callback.message.edit_text(
        "🔄 <b>Интервал синхронизации Avito</b>\n\n"
        f"Текущий: {settings.avito_sync_interval_minutes} минут\n\n"
        "Выберите новый интервал:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "edit_sheets_interval")
async def edit_sheets_interval(callback: CallbackQuery):
    """Изменить интервал Sheets"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="0 (выкл)", callback_data="set_sheets_0"),
                InlineKeyboardButton(text="5 мин", callback_data="set_sheets_5"),
            ],
            [
                InlineKeyboardButton(text="10 мин", callback_data="set_sheets_10"),
                InlineKeyboardButton(text="30 мин", callback_data="set_sheets_30"),
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="settings_sync")],
        ]
    )

    await callback.message.edit_text(
        "📊 <b>Интервал синхронизации Google Sheets</b>\n\n"
        f"Текущий: {settings.sheets_sync_interval_minutes} минут\n\n"
        "Выберите новый интервал:",
        reply_markup=keyboard,
        parse_mode="HTML",
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

    scheduler_service.reload()

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

    scheduler_service.reload()

    status = "выключена" if interval == 0 else f"установлена на {interval} минут"

    await callback.answer(f"✅ Sheets синхронизация {status}", show_alert=True)
    await sync_settings(callback)


@router.callback_query(F.data == "settings_cleaning_time")
async def cleaning_time_settings(callback: CallbackQuery):
    """Настройки времени уведомлений об уборке"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="18:00", callback_data="set_clean_time_18:00"
                ),
                InlineKeyboardButton(
                    text="19:00", callback_data="set_clean_time_19:00"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="20:00", callback_data="set_clean_time_20:00"
                ),
                InlineKeyboardButton(
                    text="21:00", callback_data="set_clean_time_21:00"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="22:00", callback_data="set_clean_time_22:00"
                ),
                InlineKeyboardButton(
                    text="09:00 (утро)", callback_data="set_clean_time_09:00"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔔 Тест сейчас", callback_data="test_cleaning_notify"
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")],
        ]
    )

    await callback.message.edit_text(
        "⏰ <b>Время уведомлений уборщиц</b>\n\n"
        f"<b>Текущее время:</b> {settings.cleaning_notification_time}\n\n"
        "<i>💡 В это время бот будет проверять выезды на ЗАВТРА и присылать уведомления уборщицам для подтверждения.</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_clean_time_"))
async def set_cleaning_time(callback: CallbackQuery):
    """Установить время уведомлений"""

    time_str = callback.data.split("_")[3]

    # Обновляем .env файл
    update_env_variable("CLEANING_NOTIFICATION_TIME", time_str)

    # Обновляем настройки в памяти
    settings.cleaning_notification_time = time_str

    # Перезапускаем планировщик (чтобы подхватилось новое время)
    from app.services.scheduler_service import scheduler_service

    scheduler_service.reload()

    await callback.answer(f"✅ Время уведомлений: {time_str}", show_alert=True)
    await cleaning_time_settings(callback)


@router.callback_query(F.data == "test_cleaning_notify")
async def test_cleaning_notify(callback: CallbackQuery):
    """Тестовый запуск уведомлений"""
    from app.jobs.cleaning_notifier import check_and_notify_cleaners

    await callback.answer("⏳ Запускаю проверку...", show_alert=False)

    try:
        # Запускаем задачу
        await check_and_notify_cleaners()
        await callback.message.answer(
            "✅ Тестовая проверка завершена. Если были брони на завтра — уведомления отправлены."
        )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при запуске: {e}")


@router.callback_query(F.data == "settings_pricing")
async def pricing_settings(callback: CallbackQuery):
    """Настройки ценообразования"""

    auto_disc = "✅ Вкл" if settings.enable_auto_discounts else "❌ Выкл"
    avito_sync = "✅ Вкл" if settings.enable_avito_price_sync else "❌ Выкл"

    text = (
        "💰 <b>Настройки ценообразования</b>\n\n"
        f"<b>Авто-скидки (горящие):</b> {auto_disc}\n"
        f"  Завтра: -{settings.auto_discount_tomorrow_percent}%\n"
        f"  Послезавтра: -{settings.auto_discount_day_after_percent}%\n\n"
        f"<b>Авто-синхр. цен → Авито:</b> {avito_sync}\n\n"
        "<i>Цикл запускается в 09:00 и 18:00:\n"
        "1) Проверка загруженности → авто-скидки\n"
        "2) Отправка цен на Авито</i>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{'❌ Выключить' if settings.enable_auto_discounts else '✅ Включить'} авто-скидки",
                    callback_data="toggle_auto_discounts",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{'❌ Выключить' if settings.enable_avito_price_sync else '✅ Включить'} синхр. Авито",
                    callback_data="toggle_avito_price_sync",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Запустить цикл сейчас",
                    callback_data="run_pricing_cycle",
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "toggle_auto_discounts")
async def toggle_auto_discounts(callback: CallbackQuery):
    new_val = not settings.enable_auto_discounts
    settings.enable_auto_discounts = new_val
    update_env_variable("ENABLE_AUTO_DISCOUNTS", str(new_val).lower())
    status = "включены" if new_val else "выключены"
    await callback.answer(f"✅ Авто-скидки {status}", show_alert=True)
    await pricing_settings(callback)


@router.callback_query(F.data == "toggle_avito_price_sync")
async def toggle_avito_price_sync(callback: CallbackQuery):
    new_val = not settings.enable_avito_price_sync
    settings.enable_avito_price_sync = new_val
    update_env_variable("ENABLE_AVITO_PRICE_SYNC", str(new_val).lower())
    status = "включена" if new_val else "выключена"
    await callback.answer(f"✅ Синхронизация цен → Авито {status}", show_alert=True)
    await pricing_settings(callback)


@router.callback_query(F.data == "run_pricing_cycle")
async def run_pricing_cycle_now(callback: CallbackQuery):
    """Ручной запуск цикла ценообразования"""
    await callback.answer("🔄 Запускаю цикл...", show_alert=False)

    from app.jobs.pricing_job import pricing_cycle_job
    try:
        await pricing_cycle_job()
        await callback.message.answer(
            "✅ Цикл ценообразования завершён.\n"
            "Проверены авто-скидки и синхронизированы цены с Авито."
        )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    """Вернуться к настройкам"""
    await show_settings(callback)


@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    """Вернуться в админ меню"""
    from app.telegram.menus.admin import admin_menu_keyboard

    await callback.message.edit_text(
        messages.ADMIN_PANEL_TITLE,
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


def update_env_variable(key: str, value: str):
    """Обновить переменную в .env файле"""
    env_path = ".env"

    if not os.path.exists(env_path):
        return

    # Читаем файл
    with open(env_path, "r", encoding="utf-8") as f:
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
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
