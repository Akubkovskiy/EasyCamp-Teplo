"""
Скрипт для ручной синхронизации броней с Google Sheets
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import AsyncSessionLocal
from app.models import Booking
from app.services.sheets_service import sheets_service


async def sync_now():
    """Синхронизация всех броней с Google Sheets"""
    
    print("🔄 Начинаю синхронизацию с Google Sheets...")
    
    # 1. Получаем все брони из БД
    async with AsyncSessionLocal() as session:
        stmt = select(Booking).options(joinedload(Booking.house)).order_by(Booking.check_in)
        result = await session.execute(stmt)
        bookings = result.scalars().all()
    
    print(f"📊 Найдено броней в БД: {len(bookings)}")
    
    if len(bookings) == 0:
        print("⚠️  База данных пустая! Создайте хотя бы одну бронь через бота.")
        return
    
    # 2. Синхронизируем с Google Sheets
    try:
        await asyncio.to_thread(sheets_service.sync_bookings_to_sheet, bookings)
        print(f"✅ Успешно синхронизировано {len(bookings)} броней в Google Sheets!")
        print(f"🔗 Откройте таблицу: https://docs.google.com/spreadsheets/d/1yIa6KNqOpvKe4EL0V-j7__LsWWLgv1cZZLsxaJNxcxk/edit")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(sync_now())
