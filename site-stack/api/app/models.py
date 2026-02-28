from datetime import datetime, date
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class House(Base):
    __tablename__ = "houses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    base_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    short_description: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BookingRequest(Base):
    __tablename__ = "booking_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    house_id: Mapped[int | None] = mapped_column(ForeignKey("houses.id"), nullable=True)
    guest_name: Mapped[str] = mapped_column(String(120), nullable=False)
    guest_phone: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    guest_comment: Mapped[str] = mapped_column(Text, nullable=False, default="")

    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    guests_count: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="website")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
