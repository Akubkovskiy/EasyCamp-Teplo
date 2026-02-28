from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from .database import get_db
from .models import BookingRequest
from .schemas import BookingRequestOut
from .audit import log_action

router = APIRouter(prefix="/admin/bookings", tags=["admin-bookings"])


class BookingCreate(BaseModel):
    house_id: int | None = None
    guest_name: str = Field(min_length=2, max_length=120)
    guest_phone: str = Field(min_length=10, max_length=32)
    guest_comment: str = Field(default="", max_length=2000)
    check_in: date
    check_out: date
    guests_count: int = Field(default=2, ge=1, le=20)
    status: str = Field(default="new")

    @field_validator("check_out")
    @classmethod
    def validate_dates(cls, v: date, info):
        ci = info.data.get("check_in")
        if ci and v <= ci:
            raise ValueError("check_out must be after check_in")
        return v


class BookingUpdate(BaseModel):
    guest_name: str | None = Field(default=None, min_length=2, max_length=120)
    guest_phone: str | None = Field(default=None, min_length=10, max_length=32)
    guest_comment: str | None = Field(default=None, max_length=2000)
    check_in: date | None = None
    check_out: date | None = None
    guests_count: int | None = Field(default=None, ge=1, le=20)
    status: str | None = None


@router.get("", response_model=list[BookingRequestOut])
def admin_list_bookings(
    status: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(BookingRequest)
    filters = []
    if status:
        filters.append(BookingRequest.status == status)
    if date_from:
        filters.append(BookingRequest.check_in >= date_from)
    if date_to:
        filters.append(BookingRequest.check_out <= date_to)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(BookingRequest.created_at.desc())
    return list(db.execute(stmt).scalars().all())


@router.post("", response_model=BookingRequestOut)
def admin_create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    item = BookingRequest(**payload.model_dump())
    db.add(item)
    log_action(db, entity="booking", entity_id=None, action="create", payload=payload.model_dump(mode='json'))
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{booking_id}", response_model=BookingRequestOut)
def admin_update_booking(booking_id: int, payload: BookingUpdate, db: Session = Depends(get_db)):
    item = db.get(BookingRequest, booking_id)
    if not item:
        raise HTTPException(status_code=404, detail="Booking not found")

    data = payload.model_dump(exclude_none=True)
    if "check_in" in data and "check_out" in data:
        if data["check_out"] <= data["check_in"]:
            raise HTTPException(status_code=400, detail="check_out must be after check_in")

    for k, v in data.items():
        setattr(item, k, v)

    log_action(db, entity="booking", entity_id=item.id, action="update", payload=data)
    db.commit()
    db.refresh(item)
    return item
