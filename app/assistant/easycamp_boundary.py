"""Concrete read boundary built from existing EasyCamp business services.

This module is deliberately not imported by ``app.main``. It is the
composition point for a future runtime: the model-facing gateway receives this
boundary, while only this boundary knows that EasyCamp currently uses an
``AsyncSession`` and the existing service classes.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING
from typing import Any, Callable, Sequence

from app.assistant.contracts import (
    BookingSource,
    BookingStatus,
    CalculateStayTotalArgs,
    CheckAvailabilityArgs,
    DateRange,
    GetPriceCalendarArgs,
    ListBookingSummariesArgs,
    RevenueSummaryArgs,
)
from app.assistant.gateway import (
    AvailabilityRecord,
    BookingRecord,
    BoundaryError,
    BoundaryRead,
    HouseRecord,
    NightlyPriceRecord,
    PriceDayRecord,
    ReadBoundary,
    RevenueRecord,
    StayTotalRecord,
)
from app.services.booking_service import BookingService
from app.services.house_service import HouseService
from app.services.pricing_service import PricingService


Clock = Callable[[], datetime]


class EasyCampBusinessReadBoundary(ReadBoundary):
    """Adapt EasyCamp read services to the assistant's typed boundary.

    The injected ``db`` is consumed only by existing business services. It is
    never passed to the model or the model-facing gateway contract.
    """

    ACTIVE_REVENUE_STATUSES = {
        BookingStatus.NEW,
        BookingStatus.CONFIRMED,
        BookingStatus.PAID,
        BookingStatus.CHECKING_IN,
        BookingStatus.CHECKED_IN,
        BookingStatus.COMPLETED,
    }

    def __init__(
        self,
        db: Any,
        *,
        clock: Clock | None = None,
        stale_after_seconds: int = 60,
    ) -> None:
        self._db = db
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._stale_after_seconds = stale_after_seconds

    async def list_houses(self) -> BoundaryRead[Sequence[HouseRecord]]:
        houses = await HouseService.get_all_houses(self._db)
        return self._read(
            [
                HouseRecord(
                    house_id=house.id,
                    name=house.name,
                    capacity=house.capacity,
                    # House has no active column in the current schema; every
                    # row returned by the catalog service is operational.
                    active=True,
                )
                for house in houses
            ]
        )

    async def check_availability(
        self, args: CheckAvailabilityArgs
    ) -> BoundaryRead[Sequence[AvailabilityRecord]]:
        houses = list(await HouseService.get_all_houses(self._db))
        if args.house_id is not None:
            houses = [house for house in houses if house.id == args.house_id]
            if not houses:
                raise BoundaryError("not_found", "Домик не найден.")

        items: list[AvailabilityRecord] = []
        for house in houses:
            fits_capacity = args.guests_count is None or house.capacity >= args.guests_count
            available = fits_capacity
            if fits_capacity:
                available = await BookingService.check_availability(
                    self._db,
                    house_id=house.id,
                    check_in=args.date_range.start,
                    check_out=args.date_range.end,
                )

            price = await PricingService.calculate_stay_total(
                self._db,
                house_id=house.id,
                check_in=args.date_range.start,
                check_out=args.date_range.end,
            )
            items.append(
                AvailabilityRecord(
                    house_id=house.id,
                    house_name=house.name,
                    capacity=house.capacity,
                    available=available,
                    price_total=price.get("total"),
                    minimum_nights=1,
                )
            )
        return self._read(items)

    async def get_price_calendar(
        self, args: GetPriceCalendarArgs
    ) -> BoundaryRead[Sequence[PriceDayRecord]]:
        await self._require_house(args.house_id)
        days = []
        for target_date in _nights(args.date_range):
            info = await PricingService.get_price_for_date(
                self._db, args.house_id, target_date
            )
            days.append(
                PriceDayRecord(
                    date=target_date,
                    price=info["final_price"],
                    minimum_nights=1,
                )
            )
        return self._read(days)

    async def calculate_stay_total(
        self, args: CalculateStayTotalArgs
    ) -> BoundaryRead[StayTotalRecord]:
        await self._require_house(args.house_id)
        summary = await PricingService.calculate_stay_total(
            self._db,
            house_id=args.house_id,
            check_in=args.date_range.start,
            check_out=args.date_range.end,
        )
        nightly: list[NightlyPriceRecord] = []
        for target_date in _nights(args.date_range):
            info = await PricingService.get_price_for_date(
                self._db, args.house_id, target_date
            )
            base = Decimal(str(info["price"]))
            final = Decimal(str(info["final_price"]))
            nightly.append(
                NightlyPriceRecord(
                    date=target_date,
                    price=info["final_price"],
                    discount=max(Decimal("0"), base - final),
                )
            )
        discount_total = Decimal(
            str(summary.get("total_without_discount", summary["total"]))
        ) - Decimal(str(summary["total"]))
        return self._read(
            StayTotalRecord(
                house_id=args.house_id,
                nightly_breakdown=nightly,
                discount_total=max(Decimal("0"), discount_total),
                total=summary["total"],
            )
        )

    async def list_bookings(
        self, args: ListBookingSummariesArgs
    ) -> BoundaryRead[Sequence[BookingRecord]]:
        bookings = await BookingService.get_all_bookings(self._db)
        rows = [
            self._booking_record(booking)
            for booking in bookings
            if _booking_matches(booking, args)
        ]
        return self._read(rows)

    async def get_revenue_summary(
        self, args: RevenueSummaryArgs
    ) -> BoundaryRead[RevenueRecord]:
        bookings = await BookingService.get_all_bookings(self._db)
        houses = await HouseService.get_all_houses(self._db)
        selected = [
            booking
            for booking in bookings
            if _revenue_booking_matches(booking, args)
        ]

        gross = sum((_decimal(booking.total_price) for booking in selected), Decimal("0"))
        advance = sum(
            (_decimal(booking.advance_amount) for booking in selected), Decimal("0")
        )
        remainder = sum(
            (
                max(
                    Decimal("0"),
                    _decimal(booking.total_price) - _decimal(booking.advance_amount),
                )
                for booking in selected
            ),
            Decimal("0"),
        )
        commission = sum(
            (_decimal(booking.commission) for booking in selected), Decimal("0")
        )
        nights = sum(
            _overlap_nights(booking.check_in, booking.check_out, args.date_range)
            for booking in selected
        )
        denominator = max(0, len(houses)) * (args.date_range.end - args.date_range.start).days
        occupancy_rate = min(1.0, nights / denominator) if denominator else 0.0
        adr = gross / nights if nights else None
        nights_to_target = _nights_to_target(args.target, gross, adr)

        return self._read(
            RevenueRecord(
                booking_count=len(selected),
                nights=nights,
                gross_booked=gross,
                advance_received=advance,
                remainder_due=remainder,
                commission=commission,
                # Cleaning and non-booking costs are not exposed by the current
                # read service boundary, so profit remains explicitly unknown.
                cleaning_cost=None,
                profit_estimate=None,
                occupancy_rate=occupancy_rate,
                adr=adr,
                nights_to_target=nights_to_target,
                calculation_status="partial",
            )
        )

    async def _require_house(self, house_id: int) -> Any:
        house = await HouseService.get_house_by_id(self._db, house_id)
        if house is None:
            raise BoundaryError("not_found", "Домик не найден.")
        return house

    def _booking_record(self, booking: Any) -> BookingRecord:
        try:
            status = BookingStatus(_enum_value(booking.status))
            source = BookingSource(_enum_value(booking.source))
        except (TypeError, ValueError) as exc:
            raise BoundaryError(
                "internal_error", "В базе найдена бронь с неизвестным статусом или источником."
            ) from exc
        house = getattr(booking, "house", None)
        return BookingRecord(
            booking_id=booking.id,
            house_id=booking.house_id,
            house_name=getattr(house, "name", None),
            check_in=booking.check_in,
            check_out=booking.check_out,
            guests_count=booking.guests_count,
            status=status,
            source=source,
            guest_name=booking.guest_name,
            guest_phone=booking.guest_phone,
            total_price=booking.total_price,
            advance_amount=booking.advance_amount,
            commission=booking.commission,
        )

    def _read(self, value: Any) -> BoundaryRead[Any]:
        return BoundaryRead(
            value=value,
            as_of=self._clock(),
            stale_after_seconds=self._stale_after_seconds,
        )


def _nights(date_range: DateRange) -> list[date]:
    return [
        date_range.start + timedelta(days=offset)
        for offset in range((date_range.end - date_range.start).days)
    ]


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _overlap_nights(check_in: date, check_out: date, date_range: DateRange) -> int:
    start = max(check_in, date_range.start)
    end = min(check_out, date_range.end)
    return max(0, (end - start).days)


def _booking_matches(booking: Any, args: ListBookingSummariesArgs) -> bool:
    status = _enum_value(booking.status)
    source = _enum_value(booking.source)
    if args.house_id is not None and booking.house_id != args.house_id:
        return False
    if args.status and status not in {item.value for item in args.status}:
        return False
    if args.source and source not in {item.value for item in args.source}:
        return False
    if not _overlap_nights(booking.check_in, booking.check_out, args.date_range):
        return False
    if args.guest_query:
        guest_name = str(booking.guest_name or "").casefold()
        if args.guest_query.casefold() not in guest_name:
            return False
    return True


def _revenue_booking_matches(booking: Any, args: RevenueSummaryArgs) -> bool:
    status = _enum_value(booking.status)
    source = _enum_value(booking.source)
    statuses = (
        {item.value for item in args.status}
        if args.status
        else {item.value for item in EasyCampBusinessReadBoundary.ACTIVE_REVENUE_STATUSES}
    )
    if status not in statuses:
        return False
    if args.house_id is not None and booking.house_id != args.house_id:
        return False
    if args.source and source not in {item.value for item in args.source}:
        return False
    return bool(_overlap_nights(booking.check_in, booking.check_out, args.date_range))


def _nights_to_target(target: Any, gross: Decimal, adr: Decimal | None) -> int | None:
    if target is None or adr is None or adr <= 0:
        return None
    target_rubles = Decimal(target.amount_minor) / Decimal("100")
    remaining = target_rubles - gross
    if remaining <= 0:
        return 0
    return int((remaining / adr).to_integral_value(rounding=ROUND_CEILING))
