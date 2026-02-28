from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from .database import get_db
from .models import BookingRequest
from .schemas import BookingRequestOut

router = APIRouter(prefix="/admin", tags=["admin"])


class BookingStatusUpdate(BaseModel):
    status: str


ALLOWED_STATUSES = {"new", "in_progress", "confirmed", "cancelled"}


@router.get("/booking-requests", response_model=list[BookingRequestOut])
def admin_list_booking_requests(
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(BookingRequest)

    if status:
        stmt = stmt.where(BookingRequest.status == status)

    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                BookingRequest.guest_name.ilike(like),
                BookingRequest.guest_phone.ilike(like),
            )
        )

    stmt = stmt.order_by(BookingRequest.created_at.desc())
    return list(db.execute(stmt).scalars().all())


@router.patch("/booking-requests/{request_id}", response_model=BookingRequestOut)
def admin_update_booking_request(request_id: int, payload: BookingStatusUpdate, db: Session = Depends(get_db)):
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {sorted(ALLOWED_STATUSES)}")

    req = db.get(BookingRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Booking request not found")

    req.status = payload.status
    db.commit()
    db.refresh(req)
    return req
