from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import GlobalSetting
from app.core.config import settings as env_settings

class SettingsService:
    @staticmethod
    async def get_all_settings(db: AsyncSession) -> dict:
        """
        Merges environment settings with database GlobalSettings.
        DB settings take precedence for 'business' logic.
        """
        # 1. Start with env defaults
        effective = env_settings.model_dump()
        
        # 2. Fetch all DB settings
        stmt = select(GlobalSetting)
        result = await db.execute(stmt)
        db_settings = result.scalars().all()
        
        # 3. Override
        for s in db_settings:
            # Only override if key exists in settings schema or is a purely dynamic key
            # We map DB keys to Settings keys directly
            if s.value is not None:
                # Handle boolean conversions if necessary
                val = s.value
                if isinstance(val, str):
                    if val.lower() == "true": val = True
                    elif val.lower() == "false": val = False
                
                effective[s.key] = val
                
        return effective

    @staticmethod
    async def get_project_settings(db: AsyncSession):
        """Helper for specifically fetching project identity"""
        all_s = await SettingsService.get_all_settings(db)
        return {
            "name": all_s.get("project_name"),
            "location": all_s.get("project_location"),
            "phone": all_s.get("contact_phone"),
            "owner": all_s.get("contact_admin_username"),
            "ai_enabled": all_s.get("ai_enabled", False), 
        }
