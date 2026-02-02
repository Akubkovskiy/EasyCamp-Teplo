from typing import List, Optional
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import House


class HouseService:
    async def get_all_houses(self) -> List[House]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(House))
            return list(result.scalars().all())

    async def get_house(self, house_id: int) -> Optional[House]:
        async with AsyncSessionLocal() as session:
            return await session.get(House, house_id)

    async def create_house(
        self, name: str, description: str = None, capacity: int = 2
    ) -> House:
        async with AsyncSessionLocal() as session:
            house = House(name=name, description=description, capacity=capacity)
            session.add(house)
            await session.commit()
            await session.refresh(house)
            return house

    async def update_house(self, house_id: int, **kwargs) -> bool:
        async with AsyncSessionLocal() as session:
            house = await session.get(House, house_id)
            if not house:
                return False
            for key, value in kwargs.items():
                if hasattr(house, key):
                    setattr(house, key, value)
            await session.commit()
            return True

    async def delete_house(self, house_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            house = await session.get(House, house_id)
            if not house:
                return False
            await session.delete(house)
            await session.commit()
            return True


house_service = HouseService()
