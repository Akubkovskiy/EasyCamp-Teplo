
import asyncio
import json
from app.services.avito_api_service import avito_api_service

async def inspect_avito_state():
    # ID from URL (House 2, 3 rooms)
    item_house2 = 4719983476 
    # ID from screenshot/wrong mapping (House 3, 2 rooms)
    item_house3 = 3792037514
    
    items = [item_house2, item_house3]
    
    print("Fetching bookings from Avito...")
    for item_id in items:
        print(f"\n--- Item {item_id} ---")
        try:
            # Fetch for Feb
            data = await asyncio.to_thread(
                avito_api_service.get_bookings,
                item_id=item_id,
                date_start="2026-02-01",
                date_end="2026-02-10"
            )
            bookings = data.get('bookings', [])
            print(f"Bookings found: {len(bookings)}")
            for b in bookings:
                print(f"  ID: {b.get('id')}, Dates: {b.get('date_start')} - {b.get('date_end')}, Type: {b.get('type')}, Status: {b.get('status')}")
                
        except Exception as e:
            print(f"Error fetching: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_avito_state())
