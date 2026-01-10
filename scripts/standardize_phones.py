"""
Скрипт для стандартизации телефонных номеров в базе данных
Приводит все номера к формату +7 (XXX) XXX-XX-XX
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Booking
from app.utils.validators import format_phone


async def main():
    """Стандартизация телефонных номеров"""
    
    print("=" * 60)
    print("СТАНДАРТИЗАЦИЯ ТЕЛЕФОННЫХ НОМЕРОВ")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Получаем все брони
        stmt = select(Booking)
        result = await session.execute(stmt)
        bookings = result.scalars().all()
        
        print(f"\nНайдено бронирований: {len(bookings)}")
        
        updated_count = 0
        
        for booking in bookings:
            old_phone = booking.guest_phone
            new_phone = format_phone(old_phone)
            
            if old_phone != new_phone:
                print(f"\nID {booking.id}: {booking.guest_name}")
                print(f"  Было:  {old_phone}")
                print(f"  Стало: {new_phone}")
                
                booking.guest_phone = new_phone
                updated_count += 1
        
        if updated_count > 0:
            await session.commit()
            print(f"\n✅ Обновлено записей: {updated_count}")
        else:
            print("\n✅ Все номера уже в стандартном формате")
    
    print("\nГотово!")


if __name__ == "__main__":
    asyncio.run(main())
