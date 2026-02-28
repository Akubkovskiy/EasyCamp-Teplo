from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import House
from .schemas import HouseOut

router = APIRouter(prefix="/admin/houses", tags=["admin-houses"])


class HouseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=120)
    capacity: int = Field(ge=1, le=20)
    base_price: int = Field(ge=0)
    short_description: str = Field(default="", max_length=300)


class HouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=120)
    capacity: int | None = Field(default=None, ge=1, le=20)
    base_price: int | None = Field(default=None, ge=0)
    short_description: str | None = Field(default=None, max_length=300)


@router.get("", response_model=list[HouseOut])
def admin_list_houses(db: Session = Depends(get_db)):
    return list(db.execute(select(House).order_by(House.id)).scalars().all())


@router.post("", response_model=HouseOut)
def admin_create_house(payload: HouseCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(House).where(House.slug == payload.slug)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")

    house = House(**payload.model_dump())
    db.add(house)
    db.commit()
    db.refresh(house)
    return house


@router.patch("/{house_id}", response_model=HouseOut)
def admin_update_house(house_id: int, payload: HouseUpdate, db: Session = Depends(get_db)):
    house = db.get(House, house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    data = payload.model_dump(exclude_none=True)
    if "slug" in data and data["slug"] != house.slug:
        existing = db.execute(select(House).where(House.slug == data["slug"])).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Slug already exists")

    for k, v in data.items():
        setattr(house, k, v)

    db.commit()
    db.refresh(house)
    return house
