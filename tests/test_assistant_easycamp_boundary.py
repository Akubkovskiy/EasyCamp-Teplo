from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.assistant.contracts import (
    AssistantRole,
    BookingSource,
    BookingStatus,
    CalculateStayTotalArgs,
    CheckAvailabilityArgs,
    GetPriceCalendarArgs,
    ListBookingSummariesArgs,
    Money,
    RevenueSummaryArgs,
    TrustedContext,
)
from app.assistant.easycamp_boundary import EasyCampBusinessReadBoundary
from app.assistant.gateway import AssistantReadOnlyGateway, BoundaryError, ReadBoundary
from app.models import BookingSource as DbBookingSource
from app.models import BookingStatus as DbBookingStatus
from app.services.booking_service import BookingService
from app.services.house_service import HouseService
from app.services.pricing_service import PricingService


NOW = datetime(2026, 9, 2, 12, tzinfo=timezone.utc)


def house(house_id: int, name: str, capacity: int):
    return SimpleNamespace(id=house_id, name=name, capacity=capacity)


def db_booking(
    booking_id: int,
    *,
    check_in: date,
    check_out: date,
    status=DbBookingStatus.CONFIRMED,
    source=DbBookingSource.DIRECT,
    guest_name="Иван Иванов",
    house_id=1,
    total=Decimal("10000"),
    advance=Decimal("2500"),
):
    return SimpleNamespace(
        id=booking_id,
        house_id=house_id,
        house=house(house_id, f"Дом {house_id}", 4),
        check_in=check_in,
        check_out=check_out,
        guests_count=2,
        status=status,
        source=source,
        guest_name=guest_name,
        guest_phone="+79990000000",
        total_price=total,
        advance_amount=advance,
        commission=Decimal("500"),
    )


@pytest.fixture
def patched_services(monkeypatch):
    houses = [house(1, "Дом 1", 4), house(2, "Дом 2", 6)]
    bookings = [
        db_booking(
            1,
            check_in=date(2026, 9, 12),
            check_out=date(2026, 9, 15),
        ),
        db_booking(
            2,
            check_in=date(2026, 10, 1),
            check_out=date(2026, 10, 3),
            status=DbBookingStatus.CANCELLED,
        ),
    ]

    async def get_all_houses(_db):
        return houses

    async def get_house_by_id(_db, house_id):
        return next((item for item in houses if item.id == house_id), None)

    async def check_availability(_db, house_id, check_in, check_out):
        return house_id == 2

    async def get_price_for_date(_db, house_id, target_date):
        assert house_id in {1, 2}
        return {
            "price": 5000,
            "final_price": 4500 if target_date.day % 2 == 0 else 5000,
        }

    async def calculate_stay_total(_db, house_id, check_in, check_out):
        return {
            "total": 9000,
            "total_without_discount": 10000,
            "nights": (check_out - check_in).days,
        }

    async def get_all_bookings(_db):
        return bookings

    monkeypatch.setattr(HouseService, "get_all_houses", staticmethod(get_all_houses))
    monkeypatch.setattr(HouseService, "get_house_by_id", staticmethod(get_house_by_id))
    monkeypatch.setattr(BookingService, "check_availability", staticmethod(check_availability))
    monkeypatch.setattr(BookingService, "get_all_bookings", staticmethod(get_all_bookings))
    monkeypatch.setattr(PricingService, "get_price_for_date", staticmethod(get_price_for_date))
    monkeypatch.setattr(
        PricingService,
        "calculate_stay_total",
        staticmethod(calculate_stay_total),
    )
    return houses, bookings


@pytest.fixture
def boundary(patched_services):
    return EasyCampBusinessReadBoundary(object(), clock=lambda: NOW)


@pytest.mark.asyncio
async def test_availability_uses_business_services_and_capacity(boundary):
    result = await boundary.check_availability(
        CheckAvailabilityArgs(
            date_range={"start": "2026-09-12", "end": "2026-09-15"},
            guests_count=5,
        )
    )

    assert [item.house_id for item in result.value] == [1, 2]
    assert result.value[0].available is False
    assert result.value[1].available is True
    assert result.value[1].price_total == 9000
    assert result.as_of == NOW


@pytest.mark.asyncio
async def test_price_calendar_and_total_normalize_existing_pricing_service(boundary):
    calendar = await boundary.get_price_calendar(
        GetPriceCalendarArgs(
            house_id=1,
            date_range={"start": "2026-09-12", "end": "2026-09-14"},
        )
    )
    assert [day.price for day in calendar.value] == [4500, 5000]

    total = await boundary.calculate_stay_total(
        CalculateStayTotalArgs(
            house_id=1,
            date_range={"start": "2026-09-12", "end": "2026-09-14"},
        )
    )
    assert len(total.value.nightly_breakdown) == 2
    assert total.value.total == 9000
    assert total.value.discount_total == 1000


@pytest.mark.asyncio
async def test_booking_filters_are_applied_before_gateway_pagination(boundary):
    result = await boundary.list_bookings(
        ListBookingSummariesArgs(
            date_range={"start": "2026-09-01", "end": "2026-09-30"},
            status=[BookingStatus.CONFIRMED],
            source=[BookingSource.DIRECT],
            guest_query="иван",
        )
    )

    assert [row.booking_id for row in result.value] == [1]
    assert result.value[0].status == BookingStatus.CONFIRMED
    assert result.value[0].source == BookingSource.DIRECT


@pytest.mark.asyncio
async def test_revenue_defaults_to_non_cancelled_statuses_and_target_math(boundary):
    result = await boundary.get_revenue_summary(
        RevenueSummaryArgs(
            date_range={"start": "2026-09-01", "end": "2026-10-01"},
            target=Money(amount_minor=30000000, currency="RUB"),
        )
    )

    assert result.value.booking_count == 1
    assert result.value.nights == 3
    assert result.value.gross_booked == Decimal("10000")
    assert result.value.nights_to_target == 88
    assert result.value.calculation_status == "partial"
    assert result.value.profit_estimate is None


@pytest.mark.asyncio
async def test_unknown_house_is_an_explicit_boundary_error(boundary):
    with pytest.raises(BoundaryError) as error:
        await boundary.get_price_calendar(
            GetPriceCalendarArgs(
                house_id=999,
                date_range={"start": "2026-09-12", "end": "2026-09-15"},
            )
        )
    assert error.value.code == "not_found"


def test_concrete_boundary_matches_injected_gateway_protocol(boundary):
    assert isinstance(boundary, ReadBoundary)


@pytest.mark.asyncio
async def test_concrete_boundary_feeds_gateway_without_database_access_in_model_layer(boundary):
    gateway = AssistantReadOnlyGateway(
        boundary,
        enabled=True,
        cursor_secret="unit-test-secret",
        clock=lambda: NOW,
    )
    context = TrustedContext(
        request_id="00000000-0000-4000-8000-000000000099",
        session_id="boundary-integration",
        actor_telegram_id=111,
        actor_role=AssistantRole.OWNER,
    )

    result = await gateway.list_booking_summaries(
        context,
        {"date_range": {"start": "2026-09-01", "end": "2026-09-30"}},
    )

    assert result.ok
    assert [row.booking_id for row in result.data.items] == [1]
