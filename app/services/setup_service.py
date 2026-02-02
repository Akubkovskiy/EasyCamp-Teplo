from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import GlobalSetting

class SetupStateService:
    @staticmethod
    async def is_initial_setup_done(db: AsyncSession) -> bool:
        """
        Проверяет, завершена ли первоначальная настройка.
        Флаг 'initial_setup_done' хранится в GlobalSetting.
        """
        stmt = select(GlobalSetting).where(GlobalSetting.key == "initial_setup_done")
        result = await db.execute(stmt)
        setting = result.scalar_one_or_none()
        
        if setting and setting.value == "true":
            return True
        return False

    @staticmethod
    async def set_initial_setup_done(db: AsyncSession, value: bool = True):
        """
        Устанавливает флаг завершения настройки.
        """
        stmt = select(GlobalSetting).where(GlobalSetting.key == "initial_setup_done")
        result = await db.execute(stmt)
        setting = result.scalar_one_or_none()
        
        if not setting:
            setting = GlobalSetting(key="initial_setup_done", value="true" if value else "false")
            db.add(setting)
        else:
            setting.value = "true" if value else "false"
        
        await db.commit()
