from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from app.telegram.auth.admin import is_admin, is_cleaner


class PanelGuardMiddleware(BaseMiddleware):
    """Глобальный guard для callback-панелей.

    Блокирует на уровне middleware вызовы callback-ов не своей роли,
    чтобы старые/чужие кнопки не открывали не тот контур меню.
    """

    ADMIN_PREFIXES = (
        "admin:",
        "bookings:",
        "booking:",
        "house:",
        "settings_",
        "set_window_",
        "set_avito_",
        "set_sheets_",
        "set_clean_time_",
        "content:",
        "users_list:",
        "user_add_start:",
        "user_remove:",
        "contacts",
    )

    CLEANER_PREFIXES = (
        "cleaner:",
    )

    async def __call__(self, handler, event: CallbackQuery, data):
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)

        callback_data = event.data or ""
        user_id = event.from_user.id if event.from_user else None
        if not user_id:
            return await handler(event, data)

        # Admin panel guard
        if callback_data.startswith(self.ADMIN_PREFIXES):
            if not is_admin(user_id):
                await event.answer("Недостаточно прав", show_alert=True)
                return

        # Cleaner panel guard
        if callback_data.startswith(self.CLEANER_PREFIXES):
            if not (is_cleaner(user_id) or is_admin(user_id)):
                await event.answer("Раздел доступен только уборщице", show_alert=True)
                return

        return await handler(event, data)
