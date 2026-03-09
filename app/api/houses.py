"""
Публичный API для домиков и цен.
Используется сайтом teplo-v-arkhyze для отображения цен и информации.
"""

from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.services.house_service import HouseService
from app.services.pricing_service import PricingService


router = APIRouter(prefix="/api/houses", tags=["houses"])


class HousePublicOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    capacity: int
    base_price: int
    current_price: int
    discount_percent: int
    discount_label: Optional[str]
    season_label: Optional[str]


class HousePriceCalendarEntry(BaseModel):
    date: date
    price: int
    final_price: int
    discount_percent: int
    season_label: Optional[str]


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("", response_model=list[HousePublicOut])
async def list_houses(db: AsyncSession = Depends(get_db)):
    """Список домиков с текущими ценами (для сайта)."""
    from app.data.house_descriptions import get_short_description

    houses = await HouseService.get_all_houses(db)
    result = []
    for house in houses:
        price_info = await PricingService.get_display_price(db, house.id)
        desc = house.description or get_short_description(house.name)
        result.append(HousePublicOut(
            id=house.id,
            name=house.name,
            description=desc,
            capacity=house.capacity,
            base_price=house.base_price,
            current_price=price_info["final_price"],
            discount_percent=price_info["discount_percent"],
            discount_label=price_info.get("discount_label"),
            season_label=price_info.get("season_label"),
        ))
    return result


@router.get("/{house_id}/prices", response_model=list[HousePriceCalendarEntry])
async def house_price_calendar(
    house_id: int,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Прайс-календарь для конкретного домика (для виджета на сайте)."""
    house = await HouseService.get_house_by_id(db, house_id)
    if not house:
        return []

    today = date.today()
    result = []
    for i in range(days):
        target = today + timedelta(days=i)
        info = await PricingService.get_price_for_date(db, house_id, target)
        result.append(HousePriceCalendarEntry(
            date=target,
            price=info["price"],
            final_price=info["final_price"],
            discount_percent=info["discount_percent"],
            season_label=info.get("season_label"),
        ))
    return result


@router.get("/{house_id}/calculate")
async def calculate_stay(
    house_id: int,
    check_in: date = Query(...),
    check_out: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Расчёт стоимости проживания (для формы бронирования на сайте)."""
    result = await PricingService.calculate_stay_total(db, house_id, check_in, check_out)
    return result
