
import asyncio
from app.services.avito_api_service import avito_api_service
import json

async def verify_status():
    item_id = 3792037514
    print(f"Checking bookings for item {item_id}...")
    
    try:
        data = await asyncio.to_thread(
            avito_api_service.get_bookings,
            item_id=item_id,
            date_start="2026-02-01",
            date_end="2026-02-10"
        )
        bookings = data.get('bookings', [])
        print(f"Found {len(bookings)} bookings:")
        for b in bookings:
            print(f"- {b['date_start']} to {b['date_end']} (Status: {b.get('status')})")
            
        # Check specific match
        target_start = "2026-02-01"
        target_end = "2026-02-07"
        match = any(b['date_start'] == target_start and b['date_end'] == target_end for b in bookings)
        print(f"Match for #14 ({target_start}-{target_end}): {match}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_status())
