from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class HouseBase(BaseModel):
    name: str
    description: Optional[str] = None
    capacity: int = 2
    base_price: int = 0

    # Dynamic Content
    wifi_info: Optional[str] = None
    address_coords: Optional[str] = None
    checkin_instruction: Optional[str] = None
    rules_text: Optional[str] = None

    # Promo
    promo_description: Optional[str] = None
    promo_image_id: Optional[str] = None
    guide_image_id: Optional[str] = None


class HouseCreate(HouseBase):
    pass


class HouseUpdate(HouseBase):
    name: Optional[str] = None
    capacity: Optional[int] = None
    base_price: Optional[int] = None


class HouseOut(HouseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# --- Seasonal Pricing ---

class HousePriceBase(BaseModel):
    label: str
    price_per_night: int
    date_from: date
    date_to: date

    @field_validator("price_per_night")
    @classmethod
    def validate_price(cls, v: int) -> int:
        if v < 0:
            raise ValueError("price_per_night cannot be negative")
        return v


class HousePriceCreate(HousePriceBase):
    house_id: int


class HousePriceUpdate(BaseModel):
    label: Optional[str] = None
    price_per_night: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class HousePriceOut(HousePriceBase):
    id: int
    house_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Discounts ---

class HouseDiscountBase(BaseModel):
    label: str
    discount_percent: int
    date_from: date
    date_to: date
    is_auto: bool = False


class HouseDiscountCreate(HouseDiscountBase):
    house_id: Optional[int] = None


class HouseDiscountOut(HouseDiscountBase):
    id: int
    house_id: Optional[int] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)
