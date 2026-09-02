from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.assistant.contracts import (
    AssistantRole,
    BookingSource,
    BookingStatus,
    CheckAvailabilityArgs,
    ListBookingSummariesArgs,
    PiiMode,
    TrustedContext,
)
from app.assistant.gateway import (
    AssistantReadOnlyGateway,
    AvailabilityRecord,
    BookingRecord,
    BoundaryError,
    BoundaryRead,
    HouseRecord,
    InMemoryAuditSink,
    PriceDayRecord,
)


NOW = datetime(2026, 9, 2, 12, tzinfo=timezone.utc)


def context(role: AssistantRole, telegram_id: int = 111) -> TrustedContext:
    return TrustedContext(
        request_id=uuid4(),
        session_id=f"session-{telegram_id}",
        actor_telegram_id=telegram_id,
        actor_role=role,
    )


def booking(booking_id: int, guest_name: str, guest_phone: str) -> BookingRecord:
    return BookingRecord(
        booking_id=booking_id,
        house_id=2,
        house_name="Дом 2",
        check_in=date(2026, 9, 12) + timedelta(days=booking_id),
        check_out=date(2026, 9, 15) + timedelta(days=booking_id),
        guests_count=4,
        status=BookingStatus.CONFIRMED,
        source=BookingSource.TELEGRAM,
        guest_name=guest_name,
        guest_phone=guest_phone,
        total_price=Decimal("16500.00"),
        advance_amount=Decimal("5000.00"),
        commission=Decimal("1000.00"),
    )


class FakeBoundary:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.rows = [
            booking(1, "Иван Иванов", "+79990000000"),
            booking(2, "Петр Петров", "+79991112233"),
        ]
        self.as_of = NOW
        self.failure: Exception | None = None

    def read(self, value):
        if self.failure:
            raise self.failure
        return BoundaryRead(value=value, as_of=self.as_of, stale_after_seconds=60)

    async def list_houses(self):
        self.calls.append("list_houses")
        return self.read([HouseRecord(2, "Дом 2", 4)])

    async def check_availability(self, args):
        self.calls.append("check_availability")
        return self.read([AvailabilityRecord(2, "Дом 2", 4, True, Decimal("16500.00"))])

    async def get_price_calendar(self, args):
        self.calls.append("get_price_calendar")
        return self.read([PriceDayRecord(args.date_range.start, Decimal("5500.00"))])

    async def calculate_stay_total(self, args):
        self.calls.append("calculate_stay_total")
        from app.assistant.gateway import NightlyPriceRecord, StayTotalRecord

        return self.read(
            StayTotalRecord(
                house_id=args.house_id,
                nightly_breakdown=[NightlyPriceRecord(args.date_range.start, Decimal("5500.00"))],
                total=Decimal("5500.00"),
            )
        )

    async def list_bookings(self, args):
        self.calls.append("list_bookings")
        return self.read(self.rows)

    async def get_revenue_summary(self, args):
        self.calls.append("get_revenue_summary")
        from app.assistant.gateway import RevenueRecord

        return self.read(RevenueRecord(2, 6, Decimal("33000"), Decimal("10000"), Decimal("23000")))


@pytest.fixture
def gateway():
    fake = FakeBoundary()
    return (
        AssistantReadOnlyGateway(
            fake,
            enabled=True,
            cursor_secret="unit-test-secret",
            clock=lambda: NOW,
        ),
        fake,
    )


@pytest.mark.asyncio
async def test_disabled_by_default_does_not_call_boundary():
    fake = FakeBoundary()
    audit = InMemoryAuditSink()
    gateway = AssistantReadOnlyGateway(fake, audit_sink=audit)

    result = await gateway.list_houses(context(AssistantRole.OWNER))

    assert not result.ok
    assert result.error.code == "assistant_disabled"
    assert fake.calls == []
    assert audit.events[0].outcome == "denied"


@pytest.mark.asyncio
async def test_role_scope_and_guest_booking_ids_are_server_bound(gateway):
    read_only, fake = gateway
    guest = context(AssistantRole.GUEST, telegram_id=222)

    forbidden = await read_only.list_booking_summaries(
        guest,
        {"date_range": {"start": "2026-09-01", "end": "2026-10-01"}},
    )
    assert forbidden.error.code == "forbidden"
    assert fake.calls == []

    scoped = AssistantReadOnlyGateway(
        fake,
        enabled=True,
        cursor_secret="unit-test-secret",
        scope_resolver=lambda _context: _resolved({1}),
        clock=lambda: NOW,
    )
    result = await scoped.list_booking_summaries(
        guest,
        {"date_range": {"start": "2026-09-01", "end": "2026-10-01"}},
    )
    assert result.ok
    assert [row.booking_id for row in result.data.items] == [1]

    fail_closed = AssistantReadOnlyGateway(
        fake,
        enabled=True,
        cursor_secret="unit-test-secret",
        scope_resolver=lambda _context: _resolved(None),
        clock=lambda: NOW,
    )
    unresolved = await fail_closed.list_booking_summaries(
        guest,
        {"date_range": {"start": "2026-09-01", "end": "2026-10-01"}},
    )
    assert unresolved.error.code == "forbidden"


async def _resolved(value):
    return value


@pytest.mark.asyncio
async def test_pii_is_masked_for_guest_and_full_only_for_owner(gateway):
    read_only, _fake = gateway
    owner = context(AssistantRole.OWNER)
    owner_result = await read_only.list_booking_summaries(
        owner,
        {
            "date_range": {"start": "2026-09-01", "end": "2026-10-01"},
            "pii_mode": "full",
        },
    )
    assert owner_result.data.items[0].guest_name == "Иван Иванов"
    assert owner_result.data.items[0].guest_phone == "+79990000000"
    assert owner_result.data.items[0].pii_mode == PiiMode.FULL

    guest_gateway = AssistantReadOnlyGateway(
        _fake,
        enabled=True,
        cursor_secret="unit-test-secret",
        scope_resolver=lambda _context: _resolved({1}),
        clock=lambda: NOW,
    )
    guest_result = await guest_gateway.list_booking_summaries(
        context(AssistantRole.GUEST, telegram_id=222),
        {
            "date_range": {"start": "2026-09-01", "end": "2026-10-01"},
            "pii_mode": "full",
        },
    )
    row = guest_result.data.items[0]
    assert row.guest_name == "Иван И."
    assert row.guest_phone == "+7 *** ***-00-00"
    assert row.pii_mode == PiiMode.MASKED
    assert "+79990000000" not in repr(row)


@pytest.mark.asyncio
async def test_cursor_is_paginated_and_bound_to_actor_and_filters(gateway):
    read_only, fake = gateway
    owner = context(AssistantRole.OWNER)
    first = await read_only.list_booking_summaries(
        owner,
        {
            "date_range": {"start": "2026-09-01", "end": "2026-10-01"},
            "pagination": {"limit": 1},
        },
    )
    assert first.ok
    assert first.data.page.has_more is True
    cursor = first.data.page.next_cursor
    assert cursor

    second = await read_only.list_booking_summaries(
        owner,
        {
            "date_range": {"start": "2026-09-01", "end": "2026-10-01"},
            "pagination": {"limit": 1, "cursor": cursor},
        },
    )
    assert [row.booking_id for row in second.data.items] == [2]

    other_actor = await read_only.list_booking_summaries(
        context(AssistantRole.OWNER, telegram_id=999),
        {
            "date_range": {"start": "2026-09-01", "end": "2026-10-01"},
            "pagination": {"limit": 1, "cursor": cursor},
        },
    )
    assert other_actor.error.code == "invalid_arguments"

    changed_filter = await read_only.list_booking_summaries(
        owner,
        {
            "date_range": {"start": "2026-09-01", "end": "2026-10-01"},
            "status": ["paid"],
            "pagination": {"limit": 1, "cursor": cursor},
        },
    )
    assert changed_filter.error.code == "invalid_arguments"
    assert fake.calls.count("list_bookings") == 2


@pytest.mark.asyncio
async def test_freshness_and_upstream_errors_are_explicit(gateway):
    read_only, fake = gateway
    owner = context(AssistantRole.OWNER)
    fake.as_of = NOW - timedelta(minutes=5)
    stale = await read_only.check_availability(
        owner,
        CheckAvailabilityArgs(date_range={"start": "2026-09-12", "end": "2026-09-15"}),
    )
    assert stale.ok
    assert stale.data.freshness.data_status == "stale"

    fake.failure = TimeoutError()
    timeout = await read_only.check_availability(
        owner,
        {"date_range": {"start": "2026-09-12", "end": "2026-09-15"}},
    )
    assert timeout.error.code == "upstream_timeout"
    assert timeout.error.retryable is True
    assert timeout.data is None

    fake.failure = ConnectionError()
    unavailable = await read_only.list_houses(owner)
    assert unavailable.error.code == "upstream_unavailable"
    assert unavailable.error.retryable is True


@pytest.mark.asyncio
async def test_money_is_integer_kopeks_and_audit_never_contains_raw_pii(gateway):
    read_only, fake = gateway
    audit = InMemoryAuditSink()
    read_only = AssistantReadOnlyGateway(
        fake,
        enabled=True,
        cursor_secret="unit-test-secret",
        audit_sink=audit,
        clock=lambda: NOW,
    )
    owner = context(AssistantRole.OWNER)
    result = await read_only.check_availability(
        owner,
        {"date_range": {"start": "2026-09-12", "end": "2026-09-15"}},
    )
    assert result.data.items[0].price_total.amount_minor == 1650000
    assert result.data.items[0].price_total.currency == "RUB"
    assert "+79990000000" not in repr(audit.events[0])
    assert len(audit.events[0].args_digest) == 64


@pytest.mark.asyncio
async def test_boundary_error_maps_to_declared_public_error(gateway):
    read_only, fake = gateway
    fake.failure = BoundaryError("upstream_unavailable", "private detail", retryable=True)
    result = await read_only.list_houses(context(AssistantRole.OWNER))
    assert result.error.code == "upstream_unavailable"
    assert result.error.message_public == "private detail"
    assert result.error.retryable is True


@pytest.mark.asyncio
async def test_malformed_boundary_response_fails_closed(gateway):
    read_only, fake = gateway

    async def broken_list_houses():
        fake.calls.append("list_houses")
        return None

    fake.list_houses = broken_list_houses
    result = await read_only.list_houses(context(AssistantRole.OWNER))

    assert result.error.code == "internal_error"
    assert result.data is None
