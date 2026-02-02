from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models import House
from app.schemas.house import HouseCreate, HouseUpdate

class HouseService:
    @staticmethod
    async def get_all_houses(db: AsyncSession) -> List[House]:
        result = await db.execute(select(House).order_by(House.id))
        return list(result.scalars().all())

    @staticmethod
    async def get_house_by_id(db: AsyncSession, house_id: int) -> Optional[House]:
        result = await db.execute(select(House).where(House.id == house_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_house(db: AsyncSession, house_in: HouseCreate) -> House:
        # Pydantic -> Dict -> DB Model
        data = house_in.model_dump()
        db_house = House(**data)
        db.add(db_house)
        await db.commit()
        await db.refresh(db_house)
        return db_house

    @staticmethod
    async def update_house(db: AsyncSession, house_id: int, house_in: HouseUpdate) -> Optional[House]:
        db_house = await HouseService.get_house_by_id(db, house_id)
        if not db_house:
            return None
        
        # Filter None values to avoid overwriting with nulls if that's the intent
        # Or simple update. model_dump(exclude_unset=True) is best for partial updates.
        update_data = house_in.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(db_house, key, value)
            
        await db.commit()
        await db.refresh(db_house)
        return db_house

    @staticmethod
    async def delete_house(db: AsyncSession, house_id: int) -> bool:
        stmt = delete(House).where(House.id == house_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
