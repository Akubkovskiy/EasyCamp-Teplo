"""
Обработчики для синхронизации с Avito API
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.avito_sync_service import sync_all_avito_items
from app.core.config import settings

router = Router()


@router.message(Command("fetch_avito"))
async def fetch_from_avito(message: Message):
    """Получить брони из Avito API"""

    await message.answer("🔄 Начинаю синхронизацию с Avito API...")

    try:
        # Проверка настроек
        if not settings.avito_client_id or not settings.avito_client_secret:
            await message.answer(
                "❌ <b>Avito API не настроен</b>\n\n"
                "Добавьте в .env:\n"
                "• AVITO_CLIENT_ID\n"
                "• AVITO_CLIENT_SECRET\n"
                "• AVITO_ITEM_IDS"
            )
            return

        if not settings.avito_item_ids:
            await message.answer(
                "❌ <b>ID объявлений не указаны</b>\n\n"
                "Добавьте в .env:\n"
                "<code>AVITO_ITEM_IDS=123456,789012</code>"
            )
            return

        # Парсим ID объявлений и маппинг на домики
        # Формат: item_id:house_id,item_id:house_id
        # Пример: 123456:1,789012:2,345678:3
        item_house_mapping = {}

        for pair in settings.avito_item_ids.split(","):
            pair = pair.strip()
            if ":" in pair:
                item_id, house_id = pair.split(":")
                item_house_mapping[int(item_id)] = int(house_id)
            else:
                # Если нет маппинга, используем item_id как есть и house_id=1
                item_house_mapping[int(pair)] = 1

        # Синхронизация
        stats = await sync_all_avito_items(item_house_mapping)

        await message.answer(
            f"✅ <b>Синхронизация с Avito завершена!</b>\n\n"
            f"📊 Статистика:\n"
            f"• Всего броней: {stats['total']}\n"
            f"• Новых: {len(stats['new_bookings'])}\n"
            f"• Обновлено: {len(stats['updated_bookings'])}\n"
            f"• Ошибок: {stats['errors']}\n\n"
            f"• Ошибок: {stats['errors']}\n\n"
            f"🔄 Обновляю Google таблицу..."
        )

        # 1. Отправка уведомлений (как в job)
        from app.jobs.avito_sync_job import notify_new_bookings, notify_updated_bookings

        if stats["new_bookings"]:
            await notify_new_bookings(stats["new_bookings"])

        if stats["updated_bookings"]:
            await notify_updated_bookings(stats["updated_bookings"])

        # 2. Синхронизация с таблицей
        from app.services.sheets_service import sheets_service

        await sheets_service.sync_if_needed(force=True)

        await message.answer("✅ Google таблица обновлена!")

    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка синхронизации:</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Проверьте:\n"
            f"• AVITO_CLIENT_ID и AVITO_CLIENT_SECRET в .env\n"
            f"• AVITO_ITEM_IDS правильно указаны\n"
            f"• У вас есть доступ к Avito API"
        )


@router.message(Command("avito_test"))
async def test_avito_connection(message: Message):
    """Тестирование подключения к Avito API"""

    await message.answer("🔍 Проверяю подключение к Avito API...")

    try:
        from app.services.avito_api_service import avito_api_service

        # Пытаемся получить токен (проверка авторизации)
        avito_api_service.get_access_token()

        await message.answer(
            f"✅ <b>Подключение успешно!</b>\n\n"
            f"• Access token получен\n"
            f"• User ID: {settings.avito_user_id}\n"
            f"• Токен истекает: {avito_api_service.token_expires_at}\n\n"
            f"Используйте /fetch_avito для синхронизации броней"
        )

    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка подключения:</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Проверьте credentials в .env"
        )
