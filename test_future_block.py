
import asyncio
from app.services.avito_api_service import avito_api_service

async def test_future_block():
    print("Testing future block...")
    item_id = 3792037514
    check_in = "2026-03-01"
    check_out = "2026-03-03"
    
    # 1. Block
    print(f"Blocking {check_in} - {check_out}...")
    success = await asyncio.to_thread(
        avito_api_service.block_dates,
        item_id=item_id,
        check_in=check_in,
        check_out=check_out,
        comment="DEBUG FUTURE"
    )
    print(f"Block result: {success}")
    
    # 2. Check
    print("Checking details...")
    try:
        data = await asyncio.to_thread(
            avito_api_service.get_bookings,
            item_id=item_id,
            date_start="2026-02-28",
            date_end="2026-03-05"
        )
        bookings = data.get('bookings', [])
        print(f"Found {len(bookings)} bookings:")
        for b in bookings:
            print(f"- {b['date_start']} to {b['date_end']} ({b.get('status')})")
    except Exception as e:
        print(f"Error fetching: {e}")

if __name__ == "__main__":
    asyncio.run(test_future_block())
