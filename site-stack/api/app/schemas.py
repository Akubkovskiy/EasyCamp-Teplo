from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator


class HouseOut(BaseModel):
    id: int
    name: str
    slug: str
    capacity: int
    base_price: int
    short_description: str

    class Config:
        from_attributes = True


class BookingRequestCreate(BaseModel):
    house_id: int | None = None
    guest_name: str = Field(min_length=2, max_length=120)
    guest_phone: str = Field(min_length=10, max_length=32)
    guest_comment: str = Field(default="", max_length=2000)
    check_in: date
    check_out: date
    guests_count: int = Field(default=2, ge=1, le=20)

    @field_validator("check_out")
    @classmethod
    def validate_dates(cls, v: date, info):
        check_in = info.data.get("check_in")
        if check_in and v <= check_in:
            raise ValueError("check_out must be after check_in")
        return v


class BookingRequestOut(BaseModel):
    id: int
    house_id: int | None
    guest_name: str
    guest_phone: str
    guest_comment: str
    check_in: date
    check_out: date
    guests_count: int
    status: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True
