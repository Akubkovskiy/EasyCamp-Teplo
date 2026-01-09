import os


from app.core.config import settings

def get_admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_TELEGRAM_IDS", "")
    ids = {int(x.strip()) for x in raw.split(",") if x.strip()}
    # Добавляем основного админа из конфига
    if settings.telegram_chat_id:
        ids.add(settings.telegram_chat_id)
    return ids


def is_admin(user_id: int) -> bool:
    return user_id in get_admin_ids()
