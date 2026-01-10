import asyncio
from datetime import date
from sqlalchemy import create_engine, Column, Integer, Date, String, Numeric, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column, relationship
from sqlalchemy import select, and_, or_
from enum import Enum

# --- MOCK MODELS ---
Base = declarative_base()

class BookingStatus(str, Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    house_id: Mapped[int] = mapped_column(Integer)
    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)
    status: Mapped[BookingStatus] = mapped_column(SQLEnum(BookingStatus), default=BookingStatus.NEW)

# --- REPRODUCTION LOGIC (The implementation we are testing) ---
# We will test BOTH the old logic (to reproduce failure if any) and new logic.

def check_availability_old(session, house_id, check_in, check_out):
    print(f"Testing OLD logic for {check_in} - {check_out}...")
    query = select(Booking).where(
        Booking.house_id == house_id,
        Booking.status != BookingStatus.CANCELLED,
        or_(
            and_(Booking.check_in <= check_in, Booking.check_out > check_in),     # Начинается внутри
            and_(Booking.check_in < check_out, Booking.check_out >= check_out),   # Заканчивается внутри
            and_(Booking.check_in >= check_in, Booking.check_out <= check_out)    # Полностью внутри
        )
    )
    result = session.execute(query).scalars().all()
    if result:
        print(f"  [X] CONFLICT FOUND with: {[ (b.check_in, b.check_out) for b in result ]}")
        return False
    print("  [OK] Available")
    return True

def check_availability_new(session, house_id, check_in, check_out):
    print(f"Testing NEW logic for {check_in} - {check_out}...")
    # Standard overlap: StartA < EndB AND EndA > StartB
    query = select(Booking).where(
        Booking.house_id == house_id,
        Booking.status != BookingStatus.CANCELLED,
        and_(
            Booking.check_in < check_out,
            Booking.check_out > check_in
        )
    )
    result = session.execute(query).scalars().all()
    if result:
        print(f"  [X] CONFLICT FOUND with: {[ (b.check_in, b.check_out) for b in result ]}")
        return False
    print("  [OK] Available")
    return True

# --- RUNNER ---
def run_tests():
    # Setup in-memory DB
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create dummy booking: March 1st to March 6th
    existing_booking = Booking(
        house_id=1,
        check_in=date(2024, 3, 1),
        check_out=date(2024, 3, 6),
        status=BookingStatus.CONFIRMED
    )
    session.add(existing_booking)
    session.commit()
    
    print(f"Existing booking: {existing_booking.check_in} - {existing_booking.check_out}")
    print("-" * 50)

    # Scenarios to test
    scenarios = [
        ("Switchover (6-8)", date(2024, 3, 6), date(2024, 3, 8), True),
        ("Overlap End (5-7)", date(2024, 3, 5), date(2024, 3, 7), False),
        ("Overlap Start (28feb-2mar)", date(2024, 2, 28), date(2024, 3, 2), False),
        ("Inside (2-4)", date(2024, 3, 2), date(2024, 3, 4), False),
        ("Encompassing (28feb-8mar)", date(2024, 2, 28), date(2024, 3, 8), False),
        ("Before (20-25feb)", date(2024, 2, 20), date(2024, 2, 25), True),
    ]

    for name, start, end, expected in scenarios:
        print(f"\nScenario: {name}")
        
        # Check Old
        res_old = check_availability_old(session, 1, start, end)
        if res_old != expected:
            print(f"  [!] OLD LOGIC FAILED! Expected {expected}, got {res_old}")
        
        # Check New
        res_new = check_availability_new(session, 1, start, end)
        if res_new != expected:
            print(f"  [!] NEW LOGIC FAILED! Expected {expected}, got {res_new}")

if __name__ == "__main__":
    run_tests()
