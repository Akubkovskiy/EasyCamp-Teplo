import asyncio
import sys
import os
from datetime import date, timedelta
from sqlalchemy import select

# Add project root to path
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.services.booking_service import booking_service
from app.models import House, Booking

async def main():
    print("Verifying availability check...")
    
    # Mock syncing to avoid side effects
    async def mock_sync():
        print("   [Mock] Google Sheets sync skipped")
    booking_service.sync_all_to_sheets = mock_sync
    
    async with AsyncSessionLocal() as session:
        # 1. Get a house
        result = await session.execute(select(House))
        house = result.scalars().first()
             
        if not house:
            print("No houses found in DB. Cannot verify.")
            return

        print(f"Testing with house: {house.name} (ID: {house.id})")
        
        # 2. Create a test booking
        today = date.today()
        # Use far future dates
        check_in = today + timedelta(days=300) 
        check_out = today + timedelta(days=305)
        
        booking_data = {
            'house_id': house.id,
            'guest_name': 'Test Availability Bot',
            'check_in': check_in,
            'check_out': check_out,
            'total_price': 0,
            'guest_phone': '000'
        }
        
        print(f"Creating test booking for {check_in} - {check_out}")
        booking = await booking_service.create_booking(booking_data)
        
        if not booking:
            print("Failed to create test booking")
            return
            
        try:
            # 3. Check availability for overlapping dates
            print("\n1. Checking overlapping dates (should be UNAVAILABLE)...")
            available = await booking_service.get_available_houses(check_in, check_out)
            ids = [h.id for h in available]
            
            if house.id in ids:
                print(f"ERROR: House {house.id} is available during booked dates!")
            else:
                print("SUCCESS: House is correctly marked as unavailable.")
                
            # 4. Check availability for non-overlapping dates
            print("\n2. Checking non-overlapping dates (should be AVAILABLE)...")
            free_check_in = today + timedelta(days=310)
            free_check_out = today + timedelta(days=312)
            
            available_free = await booking_service.get_available_houses(free_check_in, free_check_out)
            ids_free = [h.id for h in available_free]
            
            if house.id in ids_free:
                print("SUCCESS: House is available for free dates.")
            else:
                print(f"ERROR: House {house.id} is NOT available for free dates!")
                
        finally:
            # 5. Cleanup
            print("\nCleaning up test booking...")
            async with AsyncSessionLocal() as delete_session:
                b = await delete_session.get(Booking, booking.id)
                if b:
                    await delete_session.delete(b)
                    await delete_session.commit()
            print("Cleanup complete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
