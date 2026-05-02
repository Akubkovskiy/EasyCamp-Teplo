"""
Pydantic-схемы для Яндекс Путешествий Partner API.

Поля помечены Optional везде, где формат API требует уточнения.
Обновите после получения реальных ответов от API.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class YaTrGuest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class YaTrOrder(BaseModel):
    """Заказ из Яндекс Путешествий (нормализованная форма)."""

    order_id: str
    hotel_id: Optional[str] = None
    room_id: Optional[str] = None

    check_in: Optional[date] = None
    check_out: Optional[date] = None
    guests_count: Optional[int] = None

    guest: Optional[YaTrGuest] = None

    total_price: Optional[float] = None
    status: Optional[str] = None  # "pending" | "confirmed" | "cancelled"

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    raw: Optional[dict] = None  # Сырой ответ API для отладки


def parse_order(raw: dict) -> YaTrOrder:
    """
    Нормализует сырой ответ API в YaTrOrder.

    TODO: обновить маппинг полей после получения реального ответа от API.
    Ожидаемые поля угаданы по аналогии с другими OTA (Avito, Booking.com).
    """
    guest_data = raw.get("guest") or raw.get("contact") or {}
    guest = YaTrGuest(
        name=guest_data.get("name") or guest_data.get("full_name"),
        phone=guest_data.get("phone"),
        email=guest_data.get("email"),
    )

    # Попытка вытащить даты из нескольких возможных имён полей
    check_in_raw = (
        raw.get("check_in")
        or raw.get("check_in_date")
        or raw.get("date_from")
        or raw.get("arrival")
    )
    check_out_raw = (
        raw.get("check_out")
        or raw.get("check_out_date")
        or raw.get("date_to")
        or raw.get("departure")
    )

    def _to_date(v) -> Optional[date]:
        if not v:
            return None
        if isinstance(v, date):
            return v
        try:
            return datetime.fromisoformat(str(v)).date()
        except Exception:
            return None

    return YaTrOrder(
        order_id=str(raw.get("order_id") or raw.get("id") or ""),
        hotel_id=str(raw.get("hotel_id") or raw.get("property_id") or ""),
        room_id=str(raw.get("room_id") or raw.get("room_type_id") or ""),
        check_in=_to_date(check_in_raw),
        check_out=_to_date(check_out_raw),
        guests_count=raw.get("guests_count") or raw.get("guest_count") or 1,
        guest=guest,
        total_price=raw.get("total_price") or raw.get("amount"),
        status=raw.get("status"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at") or raw.get("modified_at"),
        raw=raw,
    )
