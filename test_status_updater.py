"""
Тестовый скрипт для проверки логики автоматического обновления статусов броней
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from datetime import date, timedelta
from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus
from sqlalchemy import select


async def test_status_updater():
    """Тестирование логики обновления статусов"""
    
    print("🧪 Testing booking status updater logic...\n")
    
    async with AsyncSessionLocal() as session:
        # Получаем все брони для анализа
        stmt = select(Booking).order_by(Booking.check_in)
        result = await session.execute(stmt)
        bookings = result.scalars().all()
        
        today = date.today()
        
        print(f"📅 Today: {today.strftime('%d.%m.%Y')}\n")
        print("=" * 80)
        
        # Анализируем каждую бронь
        for booking in bookings:
            status_change = None
            reason = ""
            
            if booking.status in [BookingStatus.CONFIRMED, BookingStatus.PAID, BookingStatus.NEW]:
                if booking.check_in <= today < booking.check_out:
                    status_change = f"{booking.status.value} → CHECKED_IN"
                    reason = "Guest should be checked in"
                elif booking.check_in < today and booking.check_out <= today:
                    status_change = f"{booking.status.value} → COMPLETED"
                    reason = "Booking is in the past"
                    
            elif booking.status == BookingStatus.CHECKED_IN:
                if booking.check_out <= today:
                    status_change = f"{booking.status.value} → COMPLETED"
                    reason = "Guest should have checked out"
            
            # Выводим информацию
            emoji = "🔄" if status_change else "✓"
            print(f"{emoji} Booking #{booking.id}")
            print(f"   Guest: {booking.guest_name}")
            print(f"   Dates: {booking.check_in.strftime('%d.%m.%Y')} - {booking.check_out.strftime('%d.%m.%Y')}")
            print(f"   Current Status: {booking.status.value}")
            
            if status_change:
                print(f"   ⚠️  CHANGE NEEDED: {status_change}")
                print(f"   Reason: {reason}")
            
            print("-" * 80)
        
        print("\n✅ Test completed!")


async def run_status_updater_manually():
    """Запустить обновление статусов вручную"""
    print("🚀 Running status updater job manually...\n")
    
    from app.jobs.status_updater_job import update_booking_statuses_job
    await update_booking_statuses_job()
    
    print("\n✅ Status updater job completed!")


if __name__ == "__main__":
    print("Choose an option:")
    print("1. Test status updater logic (dry run)")
    print("2. Run status updater job manually (will update database)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_status_updater())
    elif choice == "2":
        confirm = input("⚠️  This will update booking statuses in the database. Continue? (yes/no): ").strip().lower()
        if confirm == "yes":
            asyncio.run(run_status_updater_manually())
        else:
            print("Cancelled.")
    else:
        print("Invalid choice.")
