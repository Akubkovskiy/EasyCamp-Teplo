"""Создание тестовых броней для проверки фильтров"""
import asyncio
import os
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

# Мокаем переменные окружения
os.environ["TELEGRAM_BOT_TOKEN"] = "mock_token"
os.environ["TELEGRAM_CHAT_ID"] = "123456"

from app.database import init_db, AsyncSessionLocal
from app.avito.schemas import AvitoBookingPayload
from app.services.booking_service import create_or_update_avito_booking


async def main():
    print("Initializing database...")
    await init_db()
    
    today = date.today()
    
    # Создаем разные брони для тестирования
    test_bookings = [
        {
            "booking_id": "today_booking",
            "item_id": "house_teplo_1",
            "guest_name": "Иван Иванов",
            "guest_phone": "+79991234567",
            "guests_count": 2,
            "check_in": today,
            "check_out": today + timedelta(days=2),
            "total_price": Decimal("12000"),
            "status": "confirmed"
        },
        {
            "booking_id": "tomorrow_booking",
            "item_id": "house_teplo_2",
            "guest_name": "Петр Петров",
            "guest_phone": "+79997654321",
            "guests_count": 4,
            "check_in": today + timedelta(days=1),
            "check_out": today + timedelta(days=4),
            "total_price": Decimal("25000"),
            "status": "paid"
        },
        {
            "booking_id": "week_booking",
            "item_id": "house_teplo_1",
            "guest_name": "Мария Сидорова",
            "guest_phone": "+79995551234",
            "guests_count": 3,
            "check_in": today + timedelta(days=5),
            "check_out": today + timedelta(days=8),
            "total_price": Decimal("18000"),
            "status": "confirmed"
        },
        {
            "booking_id": "future_booking",
            "item_id": "house_teplo_2",
            "guest_name": "Алексей Смирнов",
            "guest_phone": "+79998887766",
            "guests_count": 2,
            "check_in": today + timedelta(days=14),
            "check_out": today + timedelta(days=17),
            "total_price": Decimal("20000"),
            "status": "new"
        },
        {
            "booking_id": "cancelled_booking",
            "item_id": "house_teplo_1",
            "guest_name": "Отмененная Бронь",
            "guest_phone": "+79990000000",
            "guests_count": 2,
            "check_in": today + timedelta(days=3),
            "check_out": today + timedelta(days=5),
            "total_price": Decimal("15000"),
            "status": "cancelled"
        }
    ]
    
    print(f"\nCreating {len(test_bookings)} test bookings...\n")
    
    async with AsyncSessionLocal() as session:
        for booking_data in test_bookings:
            payload = AvitoBookingPayload(**booking_data)
            booking = await create_or_update_avito_booking(session, payload)
            print(f"[OK] Created: {booking.guest_name} | {booking.check_in} - {booking.check_out} | Status: {booking.status.value}")
    
    print("\n[SUCCESS] All test bookings created successfully!")
    print("\nYou can now test:")
    print("  - 'Заезды сегодня' - should show Иван Иванов")
    print("  - 'Заезды на неделю' - should show Иван, Петр, Мария")
    print("  - 'Все активные' - should show all except cancelled")


if __name__ == "__main__":
    asyncio.run(main())
