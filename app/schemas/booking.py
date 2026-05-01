from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

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

    @field_validator("guest_name")
    @classmethod
    def validate_guest_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("guest_name cannot be empty")
        if len(v) > 150:
            raise ValueError("guest_name must be 150 characters or fewer")
        return v

    @field_validator("guest_phone")
    @classmethod
    def validate_guest_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re
        digits = re.sub(r"[^0-9]", "", v)
        if digits and len(digits) < 7:
            raise ValueError("guest_phone appears too short to be a valid number")
        return v

    @field_validator("guests_count")
    @classmethod
    def validate_guests_count(cls, v: int) -> int:
        if v < 1:
            raise ValueError("guests_count must be at least 1")
        return v

    @field_validator("check_out")
    @classmethod
    def validate_dates(cls, v: date, info) -> date:
        check_in = info.data.get("check_in")
        if check_in and v <= check_in:
            raise ValueError("check_out must be after check_in")
        return v

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
