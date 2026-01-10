"""
Скрипт для проверки данных в БД и синхронизации с Google Sheets
"""
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import AsyncSessionLocal
from app.models import Booking, House
from app.services.sheets_service import sheets_service


async def main():
    """Проверка БД и синхронизация с Google Sheets"""
    
    print("=" * 60)
    print("PROVERKA BAZY DANNYKH")
    print("=" * 60)
    
    # 1. Проверяем домики
    async with AsyncSessionLocal() as session:
        houses_result = await session.execute(select(House))
        houses = houses_result.scalars().all()
        print(f"\nDomikov v BD: {len(houses)}")
        for house in houses:
            print(f"   - {house.name} (ID: {house.id}, vmestimost: {house.capacity})")
    
    # 2. Проверяем брони
    async with AsyncSessionLocal() as session:
        stmt = select(Booking).options(joinedload(Booking.house)).order_by(Booking.check_in)
        result = await session.execute(stmt)
        bookings = result.scalars().all()
        
        print(f"\nBronej v BD: {len(bookings)}")
        
        if len(bookings) == 0:
            print("\nBaza dannykh pustaya!")
            print("   Sozdajte broni cherez bota ili ispolzujte skript create_test_bookings.py")
            return
        
        print("\nPoslednie 5 bronej:")
        for booking in bookings[:5]:
            print(f"   - ID {booking.id}: {booking.guest_name}, {booking.check_in} -> {booking.check_out}")
            print(f"     Domik: {booking.house.name}, Status: {booking.status.value}")
    
    # 3. Синхронизация с Google Sheets
    print("\n" + "=" * 60)
    print("SINKHRONIZATSIYA S GOOGLE SHEETS")
    print("=" * 60)
    
    try:
        print("\nPodklyuchayus k Google Sheets...")
        await asyncio.to_thread(sheets_service.sync_bookings_to_sheet, bookings)
        
        print(f"\nUSPESHNO! Sinkhronizovano {len(bookings)} bronej")
        print(f"\nOtkrojte tablitsu:")
        print(f"   https://docs.google.com/spreadsheets/d/1yIa6KNqOpvKe4EL0V-j7__LsWWLgv1cZZLsxaJNxcxk/edit")
        
        # 4. Создаем Dashboard
        print("\nSozdayu Dashboard...")
        await asyncio.to_thread(sheets_service.create_dashboard, bookings)
        print("Dashboard sozdan!")
        
    except Exception as e:
        print(f"\nOSHIBKA SINKHRONIZATSII:")
        print(f"   {str(e)}")
        print("\nPodrobnosti:")
        import traceback
        traceback.print_exc()
        
        print("\nVozmozhnyye prichiny:")
        print("   1. Неверный путь к google-credentials.json")
        print("   2. Service Account не имеет доступа к таблице")
        print("   3. Неверный GOOGLE_SHEETS_SPREADSHEET_ID в .env")
        print("   4. Google Sheets API не включен в проекте")


if __name__ == "__main__":
    asyncio.run(main())
