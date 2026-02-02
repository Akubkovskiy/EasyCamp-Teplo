from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models import BookingStatus, BookingSource
from app.schemas.house import HouseOut

class BookingBase(BaseModel):
    house_id: int
    check_in: date
    check_out: date
    guest_name: str
    guest_phone: Optional[str] = None
    guests_count: int = 1
    total_price: Decimal = Decimal("0.00")
    advance_amount: Decimal = Decimal("0.00")
    commission: Decimal = Decimal("0.00")
    prepayment_owner: Decimal = Decimal("0.00")
    status: BookingStatus = BookingStatus.NEW
    source: BookingSource = BookingSource.TELEGRAM

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    house_id: Optional[int] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    guests_count: Optional[int] = None
    total_price: Optional[Decimal] = None
    advance_amount: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    prepayment_owner: Optional[Decimal] = None
    status: Optional[BookingStatus] = None
    source: Optional[BookingSource] = None
    
    # Allow updating arbitrary fields if needed, but explicit is better
    # internal fields usually not updated via API:
    # external_id, created_at, updated_at

class BookingOut(BookingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    external_id: Optional[str] = None
    
    house: Optional[HouseOut] = None

    model_config = ConfigDict(from_attributes=True)
