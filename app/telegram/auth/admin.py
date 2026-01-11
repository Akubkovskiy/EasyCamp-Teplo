import os
from sqlalchemy import select
from app.core.config import settings
from app.database import AsyncSessionLocal
from app.models import User, UserRole


# Глобальный кеш пользователей
_db_admins: set[int] = set()
_db_cleaners: set[int] = set()


def get_env_admins() -> set[int]:
    """Получает админов из переменных окружения"""
    raw = os.getenv("ADMIN_TELEGRAM_IDS", "")
    ids = {int(x.strip()) for x in raw.split(",") if x.strip()}
    if settings.telegram_chat_id:
        ids.add(int(settings.telegram_chat_id))
    return ids


async def refresh_users_cache():
    """Обновляет кеш пользователей из БД"""
    global _db_admins, _db_cleaners
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        _db_admins = {u.telegram_id for u in users if u.role == UserRole.ADMIN}
        _db_cleaners = {u.telegram_id for u in users if u.role == UserRole.CLEANER}


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом (env + db)"""
    return user_id in get_env_admins() or user_id in _db_admins


def is_cleaner(user_id: int) -> bool:
    """Проверяет, является ли пользователь уборщицей"""
    return user_id in _db_cleaners


async def add_user(telegram_id: int, role: UserRole, name: str) -> bool:
    """Добавляет пользователя в БД и обновляет кеш"""
    async with AsyncSessionLocal() as session:
        # Проверяем, существует ли уже
        existing = await session.execute(select(User).where(User.telegram_id == telegram_id))
        if existing.scalar_one_or_none():
            return False
            
        user = User(telegram_id=telegram_id, role=role, name=name)
        session.add(user)
        await session.commit()
    
    await refresh_users_cache()
    return True


async def remove_user(telegram_id: int) -> bool:
    """Удаляет пользователя из БД и обновляет кеш"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return False
            
        await session.delete(user)
        await session.commit()
    
    await refresh_users_cache()
    return True


async def get_all_users() -> list[User]:
    """Возвращает всех пользователей из БД"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).order_by(User.id))
        return list(result.scalars().all())


async def get_user_name(user_id: int) -> str | None:
    """Возвращает имя пользователя из БД"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        return user.name if user else None
