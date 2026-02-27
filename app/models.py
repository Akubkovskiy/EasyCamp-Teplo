from datetime import date, datetime
from enum import Enum
from typing import Optional
from decimal import Decimal

from sqlalchemy import (
    String,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    Enum as SQLEnum,
)
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
    CHECKING_IN = "checking_in"  # Заезд сегодня
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
    wifi_info: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # SSID/Pass (multiline)
    address_coords: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Координаты
    checkin_instruction: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Код/Инструкция
    rules_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Правила

    # Промо для каталога
    promo_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    promo_image_id: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Tg File ID
    guide_image_id: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Tg File ID (схема проезда)

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
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus), default=BookingStatus.NEW
    )
    source: Mapped[BookingSource] = mapped_column(
        SQLEnum(BookingSource), default=BookingSource.DIRECT
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String, index=True
    )  # ID брони в Avito
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    CLEANER = "cleaner"
    GUEST = "guest"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, index=True, nullable=True) # Now optional for pure web admins
    username: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True) # Web login
    hashed_password: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole))
    name: Mapped[str] = mapped_column(String)  # Имя для удобства (например "Анна")
    phone: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Телефон для связи с бронями
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GlobalSetting(Base):
    __tablename__ = "global_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class CleaningTaskStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class CleaningPaymentEntryType(str, Enum):
    CLEANING_FEE = "cleaning_fee"
    SUPPLY_REIMBURSEMENT = "supply_reimbursement"
    ADJUSTMENT = "adjustment"


class PaymentStatus(str, Enum):
    ACCRUED = "accrued"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class SupplyClaimStatus(str, Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class CleaningTask(Base):
    __tablename__ = "cleaning_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True, index=True)
    house_id: Mapped[int] = mapped_column(ForeignKey("houses.id"), index=True)
    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    scheduled_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[CleaningTaskStatus] = mapped_column(
        SQLEnum(CleaningTaskStatus), default=CleaningTaskStatus.PENDING, index=True
    )

    confirm_deadline_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decline_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CleaningTaskCheck(Base):
    __tablename__ = "cleaning_task_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("cleaning_tasks.id"), index=True)
    code: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)
    is_required: Mapped[bool] = mapped_column(default=True)
    is_checked: Mapped[bool] = mapped_column(default=False)
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class CleaningTaskMedia(Base):
    __tablename__ = "cleaning_task_media"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("cleaning_tasks.id"), index=True)
    telegram_file_id: Mapped[str] = mapped_column(String)
    media_type: Mapped[str] = mapped_column(String, default="photo")
    uploaded_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SupplyAlertStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class SupplyAlert(Base):
    __tablename__ = "supply_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cleaning_tasks.id"), nullable=True, index=True)
    house_id: Mapped[Optional[int]] = mapped_column(ForeignKey("houses.id"), nullable=True, index=True)
    reported_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    items_json: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[SupplyAlertStatus] = mapped_column(SQLEnum(SupplyAlertStatus), default=SupplyAlertStatus.NEW)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class CleaningRate(Base):
    __tablename__ = "cleaning_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    house_id: Mapped[int] = mapped_column(ForeignKey("houses.id"), index=True)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    active_from: Mapped[date] = mapped_column(Date)
    active_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CleaningPaymentLedger(Base):
    __tablename__ = "cleaning_payments_ledger"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cleaning_tasks.id"), nullable=True, index=True)
    cleaner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    entry_type: Mapped[CleaningPaymentEntryType] = mapped_column(SQLEnum(CleaningPaymentEntryType))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    currency: Mapped[str] = mapped_column(String, default="RUB")
    period_key: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[PaymentStatus] = mapped_column(SQLEnum(PaymentStatus), default=PaymentStatus.ACCRUED, index=True)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class SupplyExpenseClaim(Base):
    __tablename__ = "supply_expense_claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cleaning_tasks.id"), nullable=True, index=True)
    house_id: Mapped[Optional[int]] = mapped_column(ForeignKey("houses.id"), nullable=True, index=True)
    cleaner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    purchase_date: Mapped[date] = mapped_column(Date)
    amount_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    items_json: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    receipt_photo_file_id: Mapped[str] = mapped_column(String)
    status: Mapped[SupplyClaimStatus] = mapped_column(SQLEnum(SupplyClaimStatus), default=SupplyClaimStatus.SUBMITTED, index=True)
    admin_comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
