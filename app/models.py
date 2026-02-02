from datetime import date, datetime
from enum import Enum
from typing import Optional
from decimal import Decimal

from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BookingSource(str, Enum):
    AVITO = "avito"
    TELEGRAM = "telegram"
    DIRECT = "direct"
    OTHER = "other"


class BookingStatus(str, Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CHECKED_IN = "checked_in"  # Проживает
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class House(Base):
    __tablename__ = "houses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String)
    capacity: Mapped[int] = mapped_column(Integer, default=2)
    
    # Динамический контент
    wifi_info: Mapped[Optional[str]] = mapped_column(String, nullable=True) # SSID/Pass (multiline)
    address_coords: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Координаты
    checkin_instruction: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Код/Инструкция
    rules_text: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Правила
    
    # Промо для каталога
    promo_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    promo_image_id: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Tg File ID
    guide_image_id: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Tg File ID (схема проезда)
    
    bookings: Mapped[list["Booking"]] = relationship(back_populates="house")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Связи
    house_id: Mapped[int] = mapped_column(ForeignKey("houses.id"))
    house: Mapped["House"] = relationship(back_populates="bookings")

    # Данные гостя
    guest_name: Mapped[str] = mapped_column(String)
    guest_phone: Mapped[str] = mapped_column(String)
    
    # Детали брони
    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)
    guests_count: Mapped[int] = mapped_column(Integer)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    advance_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    commission: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    prepayment_owner: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    # Метаданные
    status: Mapped[BookingStatus] = mapped_column(SQLEnum(BookingStatus), default=BookingStatus.NEW)
    source: Mapped[BookingSource] = mapped_column(SQLEnum(BookingSource), default=BookingSource.DIRECT)
    external_id: Mapped[Optional[str]] = mapped_column(String, index=True)  # ID брони в Avito
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserRole(str, Enum):
    ADMIN = "admin"
    CLEANER = "cleaner"
    GUEST = "guest"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole))
    name: Mapped[str] = mapped_column(String)  # Имя для удобства (например "Анна")
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Телефон для связи с бронями
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GlobalSetting(Base):
    __tablename__ = "global_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
