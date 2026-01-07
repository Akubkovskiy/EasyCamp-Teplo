import os


def get_admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_TELEGRAM_IDS", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def is_admin(user_id: int) -> bool:
    return user_id in get_admin_ids()
