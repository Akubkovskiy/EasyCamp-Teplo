"""Typed DTOs for the owner/admin read-only assistant foundation.

These models mirror ``teplo-assistant/contracts/read_only_v1.schema.json``.
They are transport and policy types only; none of them owns database access.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AssistantRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    CLEANER = "cleaner"
    GUEST = "guest"


class BookingStatus(str, Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CHECKING_IN = "checking_in"
    CHECKED_IN = "checked_in"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BookingSource(str, Enum):
    AVITO = "avito"
    TELEGRAM = "telegram"
    DIRECT = "direct"
    YANDEX_TRAVEL = "yandex_travel"
    OTHER = "other"


class PiiMode(str, Enum):
    MASKED = "masked"
    FULL = "full"


class DateRange(_StrictModel):
    """An overnight range: start inclusive, end exclusive."""

    start: date
    end: date

    @model_validator(mode="after")
    def validate_range(self) -> "DateRange":
        days = (self.end - self.start).days
        if days <= 0:
            raise ValueError("date range must contain at least one night")
        if days > 366:
            raise ValueError("date range cannot exceed 366 days")
        return self


class Money(_StrictModel):
    amount_minor: int = Field(ge=0)
    currency: Literal["RUB"] = "RUB"


class TrustedContext(_StrictModel):
    """Identity supplied by Telegram/runtime code, never by the model."""

    request_id: UUID
    session_id: str = Field(min_length=1, max_length=128)
    actor_telegram_id: int = Field(gt=0)
    actor_role: AssistantRole
    channel: Literal["telegram"] = "telegram"
    locale: Literal["ru-RU"] = "ru-RU"
    timezone: Literal["Europe/Moscow"] = "Europe/Moscow"


class PaginationRequest(_StrictModel):
    limit: int = Field(default=25, ge=1, le=100)
    cursor: Optional[str] = Field(default=None, max_length=2048)


class PaginationResponse(_StrictModel):
    limit: int = Field(ge=1, le=100)
    has_more: bool
    next_cursor: Optional[str] = Field(default=None, max_length=2048)


class ListHousesArgs(_StrictModel):
    """No model-controlled filters are needed for the first catalog read."""

    include_inactive: Literal[False] = False


class CheckAvailabilityArgs(_StrictModel):
    date_range: DateRange
    house_id: Optional[int] = Field(default=None, gt=0)
    guests_count: Optional[int] = Field(default=None, ge=1, le=50)


class GetPriceCalendarArgs(_StrictModel):
    house_id: int = Field(gt=0)
    date_range: DateRange


class CalculateStayTotalArgs(GetPriceCalendarArgs):
    pass


class ListBookingSummariesArgs(_StrictModel):
    date_range: DateRange
    house_id: Optional[int] = Field(default=None, gt=0)
    status: list[BookingStatus] = Field(default_factory=list, max_length=7)
    source: list[BookingSource] = Field(default_factory=list, max_length=5)
    guest_query: Optional[str] = Field(default=None, min_length=1, max_length=100)
    pii_mode: PiiMode = PiiMode.MASKED
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)

    @model_validator(mode="after")
    def validate_filters(self) -> "ListBookingSummariesArgs":
        if len(set(self.status)) != len(self.status):
            raise ValueError("status filters must be unique")
        if len(set(self.source)) != len(self.source):
            raise ValueError("source filters must be unique")
        return self


class RevenueSummaryArgs(_StrictModel):
    date_range: DateRange
    house_id: Optional[int] = Field(default=None, gt=0)
    source: list[BookingSource] = Field(default_factory=list, max_length=5)
    status: list[BookingStatus] = Field(default_factory=list, max_length=7)
    target: Optional[Money] = None

    @model_validator(mode="after")
    def validate_filters(self) -> "RevenueSummaryArgs":
        if len(set(self.status)) != len(self.status):
            raise ValueError("status filters must be unique")
        if len(set(self.source)) != len(self.source):
            raise ValueError("source filters must be unique")
        return self


class Freshness(_StrictModel):
    source_system: Literal["easycamp"] = "easycamp"
    data_status: Literal["fresh", "stale"]
    as_of: datetime
    stale_after_seconds: int = Field(default=60, ge=0)

    @model_validator(mode="after")
    def require_timezone(self) -> "Freshness":
        if self.as_of.tzinfo is None:
            raise ValueError("as_of must include a timezone")
        return self


class HouseView(_StrictModel):
    house_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=120)
    capacity: int = Field(ge=1, le=50)
    active: bool


class AvailabilityView(_StrictModel):
    house_id: int = Field(gt=0)
    house_name: str = Field(min_length=1, max_length=120)
    capacity: int = Field(ge=1, le=50)
    available: bool
    price_total: Optional[Money]
    blocked_dates: list[date] = Field(default_factory=list)
    minimum_nights: int = Field(default=1, ge=1)


class PriceDayView(_StrictModel):
    date: date
    price: Money
    minimum_nights: int = Field(default=1, ge=1)


class NightlyPriceView(_StrictModel):
    date: date
    price: Money
    discount: Optional[Money] = None


class BookingSummaryView(_StrictModel):
    booking_id: int = Field(gt=0)
    house_id: int = Field(gt=0)
    house_name: Optional[str] = Field(default=None, max_length=120)
    check_in: date
    check_out: date
    nights: int = Field(ge=1)
    guests_count: int = Field(ge=1)
    status: BookingStatus
    source: BookingSource
    guest_name: Optional[str] = Field(default=None, max_length=200)
    guest_phone: Optional[str] = Field(default=None, max_length=32)
    total_price: Money
    advance_received: Money
    remainder_due: Money
    commission: Optional[Money] = None
    pii_mode: PiiMode


class AvailabilityData(_StrictModel):
    query: DateRange
    items: list[AvailabilityView]
    freshness: Freshness


class HouseListData(_StrictModel):
    items: list[HouseView]
    freshness: Freshness


class PriceCalendarData(_StrictModel):
    house_id: int = Field(gt=0)
    days: list[PriceDayView]
    freshness: Freshness


class StayTotalData(_StrictModel):
    house_id: int = Field(gt=0)
    nights: int = Field(ge=1)
    nightly_breakdown: list[NightlyPriceView]
    discount_total: Money
    total: Money
    freshness: Freshness


class BookingListData(_StrictModel):
    items: list[BookingSummaryView]
    page: PaginationResponse
    freshness: Freshness


class RevenueSummaryData(_StrictModel):
    date_range: DateRange
    booking_count: int = Field(ge=0)
    nights: int = Field(ge=0)
    gross_booked: Money
    advance_received: Money
    remainder_due: Money
    commission: Optional[Money] = None
    cleaning_cost: Optional[Money] = None
    profit_estimate: Optional[Money] = None
    occupancy_rate: float = Field(ge=0, le=1)
    adr: Optional[Money] = None
    nights_to_target: Optional[int] = Field(default=None, ge=0)
    calculation_status: Literal["complete", "partial", "unavailable"]
    freshness: Freshness


class ToolError(_StrictModel):
    code: Literal[
        "assistant_disabled",
        "unauthorized",
        "forbidden",
        "invalid_arguments",
        "ambiguous_reference",
        "not_found",
        "upstream_unavailable",
        "upstream_timeout",
        "stale_data",
        "rate_limited",
        "internal_error",
    ]
    message_public: str = Field(min_length=1, max_length=500)
    retryable: bool
    request_id: UUID
    field_errors: list[dict[str, str]] = Field(default_factory=list, max_length=20)


class AuditEvent(_StrictModel):
    event_id: UUID
    request_id: UUID
    session_id: str = Field(max_length=128)
    actor_telegram_id: int = Field(gt=0)
    actor_role: AssistantRole
    tool_name: str = Field(max_length=80)
    mode: Literal["read_only"] = "read_only"
    outcome: Literal["success", "error", "denied"]
    created_at: datetime
    args_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    pii_mode: PiiMode = PiiMode.MASKED
    result_count: Optional[int] = Field(default=None, ge=0)
    error_code: Optional[str] = None


class AssistantDraft(_StrictModel):
    """Shared future write shape; no v1 tool creates or consumes this model."""

    draft_id: UUID
    kind: Literal["booking_create", "booking_update", "booking_cancel", "cleaning_update"]
    status: Literal["prepared", "confirmed", "executed", "expired", "cancelled", "failed"]
    actor_telegram_id: int = Field(gt=0)
    actor_role: AssistantRole
    plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    expires_at: datetime
    confirmation_attempts: int = Field(default=0, ge=0)
    result_booking_id: Optional[int] = Field(default=None, gt=0)
