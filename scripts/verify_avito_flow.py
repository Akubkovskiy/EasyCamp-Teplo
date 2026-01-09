import asyncio
import sys
import os
from datetime import date, timedelta

# Добавляем корень проекта в путь
sys.path.append(os.getcwd())

# Mock env vars BEFORE importing config
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
os.environ["TELEGRAM_CHAT_ID"] = "123456789"

from app.database import init_db, AsyncSessionLocal
from app.services.booking_service import create_or_update_avito_booking
from app.avito.schemas import AvitoBookingPayload
from app.models import Booking
from sqlalchemy import select

async def main():
    print("Starting verification...")
    
    # 1. Init DB
    await init_db()
    print("Database initialized")
    
    # 2. Mock Avito Payload
    payload = AvitoBookingPayload(
        booking_id="test_booking_123",
        item_id="house_1",
        guest_name="Test Parent",
        guest_phone="+79991234567",
        guests_count=3,
        check_in=date.today(),
        check_out=date.today() + timedelta(days=2),
        total_price=15000,
        status="confirmed"
    )
    
    # 3. Call Service directly (simulating webhook)
    async with AsyncSessionLocal() as session:
        booking = await create_or_update_avito_booking(session, payload)
        print(f"Booking created: ID={booking.id}, Guest={booking.guest_name}")
        
    # 4. Verify in DB
    async with AsyncSessionLocal() as session:
        stmt = select(Booking).where(Booking.external_id == "test_booking_123")
        result = await session.execute(stmt)
        saved_booking = result.scalar_one_or_none()
        
        if saved_booking:
            print(f"Verification successful! Found booking in DB: {saved_booking.guest_name}")
            print(f"   Dates: {saved_booking.check_in} - {saved_booking.check_out}")
            print(f"   Status: {saved_booking.status}")
        else:
            print("Verification failed! Booking not found in DB")

if __name__ == "__main__":
    asyncio.run(main())
