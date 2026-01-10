
import asyncio
import logging
from datetime import date, datetime
from sqlalchemy import select, or_, and_

from app.database import AsyncSessionLocal
from app.models import Booking, BookingStatus

# Configure logging to see SQL queries
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

async def test_availability():
    async with AsyncSessionLocal() as session:
        # 1. Inspect existing bookings for Teplo 2 (House ID 2) or whatever house has the issue
        # User mentioned Mar 6. Let's look for bookings around Mar 6.
        print("\n--- Examining Existing Bookings ---")
        stmt = select(Booking).where(Booking.check_in >= date(2026, 3, 1), Booking.check_in <= date(2026, 3, 15))
        result = await session.execute(stmt)
        bookings = result.scalars().all()
        for b in bookings:
            print(f"Booking {b.id}: House {b.house_id}, {b.check_in} - {b.check_out} ({b.status})")

        # 2. Test Check Logic
        house_id = 2  # Assuming house 2 based on previous logs/screenshots
        check_in = date(2026, 3, 6)
        check_out = date(2026, 3, 8)
        
        print(f"\n--- Testing Availability for House {house_id}: {check_in} - {check_out} ---")
        
        # Replicating logic from booking_service.py
        query = select(Booking).where(
            Booking.house_id == house_id,
            Booking.status != BookingStatus.CANCELLED,
            or_(
                and_(Booking.check_in <= check_in, Booking.check_out > check_in),     # Inside Start
                and_(Booking.check_in < check_out, Booking.check_out >= check_out),   # Inside End
                and_(Booking.check_in >= check_in, Booking.check_out <= check_out)    # Fully Inside
            )
        )
        
        result = await session.execute(query)
        conflicts = result.scalars().all()
        
        if conflicts:
            print("❌ CONFLICT FOUND:")
            for c in conflicts:
                print(f"  Conflict with Booking {c.id}: {c.check_in} - {c.check_out}")
                
                # Analyze why
                cond1 = (c.check_in <= check_in) and (c.check_out > check_in)
                cond2 = (c.check_in < check_out) and (c.check_out >= check_out)
                cond3 = (c.check_in >= check_in) and (c.check_out <= check_out)
                print(f"    Cond1 (Start overlap): {cond1} ({c.check_in} <= {check_in} and {c.check_out} > {check_in})")
                print(f"    Cond2 (End overlap):   {cond2} ({c.check_in} < {check_out} and {c.check_out} >= {check_out})")
                print(f"    Cond3 (Inside):        {cond3}")
        else:
            print("✅ NO CONFLICTS FOUND")

if __name__ == "__main__":
    asyncio.run(test_availability())
