from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from decimal import Decimal
from typing import Optional

from app.database import get_db
from app.web.deps import get_current_admin
from app.services.booking_service import BookingService
from app.services.house_service import HouseService
from app.models import BookingStatus, BookingSource
from app.schemas.booking import BookingUpdate

templates = Jinja2Templates(directory="app/web/templates")

# Добавляем фильтр для форматирования телефона
def format_phone(phone: str) -> str:
    """Форматирует телефон в вид +7 (XXX) XXX-XX-XX"""
    if not phone:
        return ""
    # Убираем все нечисловые символы
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) == 11 and digits.startswith('7'):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    elif len(digits) == 10:
        return f"+7 ({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
    return phone

templates.env.filters['format_phone'] = format_phone

router = APIRouter(prefix="/admin-web/bookings", tags=["web-bookings"])


@router.get("", response_class=HTMLResponse)
async def list_bookings(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """
    Список всех бронирований.
    """
    bookings = await BookingService.get_all_bookings(db)
    
    return templates.TemplateResponse(
        "bookings/list.html",
        {
            "request": request,
            "bookings": bookings,
            "user": admin,
            "title": "Управление бронированиями",
            "active_tab": "bookings"
        },
    )


@router.get("/{booking_id}", response_class=HTMLResponse)
async def view_booking(
    request: Request,
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """
    Просмотр деталей бронирования.
    """
    booking = await BookingService.get_booking(db, booking_id)
    if not booking:
        return RedirectResponse(url="/admin-web/bookings", status_code=303)
    
    # Получить список домов для выпадающего списка
    houses = await HouseService.get_all_houses(db)
    
    return templates.TemplateResponse(
        "bookings/detail.html",
        {
            "request": request,
            "booking": booking,
            "houses": houses,
            "user": admin,
            "title": f"Бронь #{booking.id}",
            "active_tab": "bookings",
            "BookingStatus": BookingStatus,
            "BookingSource": BookingSource,
        },
    )


@router.post("/{booking_id}", response_class=HTMLResponse)
async def update_booking(
    request: Request,
    booking_id: int,
    house_id: int = Form(...),
    guest_name: str = Form(...),
    guest_phone: str = Form(...),
    check_in: date = Form(...),
    check_out: date = Form(...),
    guests_count: int = Form(...),
    total_price: Decimal = Form(...),
    advance_amount: Decimal = Form(0),
    commission: Decimal = Form(0),
    prepayment_owner: Decimal = Form(0),
    status: str = Form(...),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """
    Обновление бронирования.
    """
    try:
        update_data = BookingUpdate(
            house_id=house_id,
            guest_name=guest_name,
            guest_phone=guest_phone,
            check_in=check_in,
            check_out=check_out,
            guests_count=guests_count,
            total_price=total_price,
            advance_amount=advance_amount,
            commission=commission,
            prepayment_owner=prepayment_owner,
            status=BookingStatus(status),
        )
        
        success = await BookingService.update_booking(db, booking_id, update_data)
        
        if success:
            return RedirectResponse(
                url=f"/admin-web/bookings/{booking_id}",
                status_code=status.HTTP_303_SEE_OTHER
            )
        else:
            return RedirectResponse(
                url="/admin-web/bookings",
                status_code=status.HTTP_303_SEE_OTHER
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error updating booking {booking_id}: {e}", exc_info=True)
        return RedirectResponse(
            url=f"/admin-web/bookings/{booking_id}?error=update_failed",
            status_code=status.HTTP_303_SEE_OTHER
        )
