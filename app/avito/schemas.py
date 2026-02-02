from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class AvitoBookingPayload(BaseModel):
    """
    Примерная структура payload брони от Avito.
    Нужно уточнить реальные поля из документации Avito API.
    """

    booking_id: str = Field(..., description="ID брони в Avito")
    item_id: str = Field(..., description="ID объявления")

    guest_name: str = Field(..., description="Имя гостя")
    guest_phone: str = Field(..., description="Телефон гостя")
    guests_count: int = Field(1, description="Количество гостей")

    check_in: date
    check_out: date

    total_price: Decimal = Field(0, description="Общая стоимость")
    status: str = Field(..., description="Статус брони (created, confirmed, etc)")


class AvitoWebhookEvent(BaseModel):
    event_type: str
    event_time: int
    payload: dict
