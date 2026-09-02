"""Read-only assistant gateway over EasyCamp business-service boundaries.

The gateway intentionally knows nothing about SQLAlchemy or Telegram. A
boundary implementation is injected by the future runtime and is expected to
delegate to existing EasyCamp services such as HouseService, PricingService and
BookingService. The default is disabled, so importing this module has no side
effects and cannot query production state.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    TypeVar,
    runtime_checkable,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError

from app.assistant.contracts import (
    AssistantRole,
    AuditEvent,
    AvailabilityData,
    AvailabilityView,
    BookingListData,
    BookingSource,
    BookingStatus,
    BookingSummaryView,
    CalculateStayTotalArgs,
    CheckAvailabilityArgs,
    DateRange,
    Freshness,
    GetPriceCalendarArgs,
    HouseListData,
    HouseView,
    ListBookingSummariesArgs,
    ListHousesArgs,
    Money,
    NightlyPriceView,
    PaginationResponse,
    PiiMode,
    PriceCalendarData,
    PriceDayView,
    RevenueSummaryArgs,
    RevenueSummaryData,
    StayTotalData,
    ToolError,
    TrustedContext,
)


class BoundaryError(Exception):
    """Safe error from an EasyCamp business boundary."""

    def __init__(self, code: str, message_public: str, retryable: bool = False) -> None:
        super().__init__(message_public)
        self.code = code
        self.message_public = message_public
        self.retryable = retryable


@dataclass(frozen=True)
class HouseRecord:
    house_id: int
    name: str
    capacity: int
    active: bool = True


@dataclass(frozen=True)
class AvailabilityRecord:
    house_id: int
    house_name: str
    capacity: int
    available: bool
    price_total: Decimal | int | None
    blocked_dates: Sequence[date] = ()
    minimum_nights: int = 1


@dataclass(frozen=True)
class PriceDayRecord:
    date: date
    price: Decimal | int
    minimum_nights: int = 1


@dataclass(frozen=True)
class NightlyPriceRecord:
    date: date
    price: Decimal | int
    discount: Decimal | int | None = None


@dataclass(frozen=True)
class BookingRecord:
    booking_id: int
    house_id: int
    house_name: str | None
    check_in: date
    check_out: date
    guests_count: int
    status: BookingStatus | str
    source: BookingSource | str
    guest_name: str | None
    guest_phone: str | None
    total_price: Decimal | int
    advance_amount: Decimal | int
    commission: Decimal | int | None = None


@dataclass(frozen=True)
class StayTotalRecord:
    house_id: int
    nightly_breakdown: Sequence[NightlyPriceRecord]
    discount_total: Decimal | int = 0
    total: Decimal | int = 0


@dataclass(frozen=True)
class RevenueRecord:
    booking_count: int
    nights: int
    gross_booked: Decimal | int
    advance_received: Decimal | int
    remainder_due: Decimal | int
    commission: Decimal | int | None = None
    cleaning_cost: Decimal | int | None = None
    profit_estimate: Decimal | int | None = None
    occupancy_rate: float = 0.0
    adr: Decimal | int | None = None
    nights_to_target: int | None = None
    calculation_status: str = "complete"


T = TypeVar("T")


@dataclass(frozen=True)
class BoundaryRead(Generic[T]):
    value: T
    as_of: datetime
    stale_after_seconds: int = 60


@runtime_checkable
class ReadBoundary(Protocol):
    """Business-service boundary; implementations must not expose a DB handle.

    ``list_bookings`` applies its date/status/source/name filters. The gateway
    adds the actor scope as a defensive second filter.
    """

    async def list_houses(self) -> BoundaryRead[Sequence[HouseRecord]]: ...

    async def check_availability(
        self, args: CheckAvailabilityArgs
    ) -> BoundaryRead[Sequence[AvailabilityRecord]]: ...

    async def get_price_calendar(
        self, args: GetPriceCalendarArgs
    ) -> BoundaryRead[Sequence[PriceDayRecord]]: ...

    async def calculate_stay_total(
        self, args: CalculateStayTotalArgs
    ) -> BoundaryRead[StayTotalRecord]: ...

    async def list_bookings(
        self, args: ListBookingSummariesArgs
    ) -> BoundaryRead[Sequence[BookingRecord]]: ...

    async def get_revenue_summary(
        self, args: RevenueSummaryArgs
    ) -> BoundaryRead[RevenueRecord]: ...


class AuditSink(Protocol):
    async def record(self, event: AuditEvent) -> None: ...


class InMemoryAuditSink:
    """Test-only sink; production persistence belongs to a later migration."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def record(self, event: AuditEvent) -> None:
        self.events.append(event)


class _NullAuditSink:
    async def record(self, event: AuditEvent) -> None:
        return None


ScopeResolver = Callable[[TrustedContext], Awaitable[Optional[set[int]]]]
Clock = Callable[[], datetime]


@dataclass(frozen=True)
class ToolResult(Generic[T]):
    request_id: UUID
    data: T | None = None
    error: ToolError | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict[str, Any]:
        if self.error is not None:
            return {
                "ok": False,
                "request_id": str(self.request_id),
                "error": self.error.model_dump(mode="json"),
            }
        if isinstance(self.data, BaseModel):
            data = self.data.model_dump(mode="json")
        else:
            data = self.data
        return {"ok": True, "request_id": str(self.request_id), "data": data}


class _CursorCodec:
    VERSION = 1

    def __init__(self, secret: str, clock: Clock, ttl_seconds: int) -> None:
        self._secret = secret.encode("utf-8")
        self._clock = clock
        self._ttl_seconds = ttl_seconds

    def issue(
        self,
        context: TrustedContext,
        filter_digest: str,
        offset: int,
        limit: int,
    ) -> str:
        payload = {
            "v": self.VERSION,
            "actor": context.actor_telegram_id,
            "role": context.actor_role.value,
            "session": context.session_id,
            "filter": filter_digest,
            "offset": offset,
            "limit": limit,
            "exp": int(self._clock().timestamp()) + self._ttl_seconds,
        }
        body = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
        signature = hmac.new(self._secret, body.encode("ascii"), hashlib.sha256).hexdigest()
        return f"{body}.{signature}"

    def read(
        self,
        token: str,
        context: TrustedContext,
        filter_digest: str,
    ) -> tuple[int, int] | None:
        try:
            body, signature = token.split(".", 1)
            expected = hmac.new(self._secret, body.encode("ascii"), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                return None
            payload = json.loads(_b64url_decode(body))
            if (
                payload.get("v") != self.VERSION
                or payload.get("actor") != context.actor_telegram_id
                or payload.get("role") != context.actor_role.value
                or payload.get("session") != context.session_id
                or payload.get("filter") != filter_digest
                or int(payload.get("exp", 0)) < int(self._clock().timestamp())
            ):
                return None
            offset = int(payload["offset"])
            limit = int(payload["limit"])
            if offset < 0 or limit < 1 or limit > 100:
                return None
            return offset, limit
        except (ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
            return None


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _money(value: Decimal | int | None) -> Money | None:
    if value is None:
        return None
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount < 0:
        raise ValueError("negative amount is not valid for this DTO")
    return Money(amount_minor=int(amount * 100), currency="RUB")


def _freshness(read: BoundaryRead[Any], now: datetime) -> Freshness:
    as_of = read.as_of
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    current = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    age = max(0.0, (current - as_of).total_seconds())
    status = "fresh" if age <= read.stale_after_seconds else "stale"
    return Freshness(
        source_system="easycamp",
        data_status=status,
        as_of=as_of,
        stale_after_seconds=read.stale_after_seconds,
    )


def _filter_digest(args: ListBookingSummariesArgs) -> str:
    data = args.model_dump(mode="json")
    data["pagination"]["cursor"] = None
    return _json_digest(data)


def _json_digest(value: Any) -> str:
    """Hash normalized arguments without retaining their values in audit data."""
    return hashlib.sha256(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()


def _model_digest(value: BaseModel) -> str:
    return _json_digest(value.model_dump(mode="json"))


def _input_digest(value: BaseModel | Mapping[str, Any]) -> str:
    try:
        normalized = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
        return _json_digest(normalized)
    except (TypeError, ValueError):
        return _json_digest({"unserializable": type(value).__name__})


def _mask_name(value: str | None) -> str | None:
    if not value:
        return None
    parts = value.strip().split()
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0][0] + "***"
    return f"{parts[0]} {parts[1][0]}."


def _mask_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(char for char in value if char.isdigit())
    if len(digits) >= 11 and digits[0] in "78":
        prefix = "+7"
        tail = digits[-4:]
        return f"{prefix} *** ***-{tail[:2]}-{tail[2:]}"
    if len(digits) >= 4:
        return f"*** ***-{digits[-4:-2]}-{digits[-2:]}"
    return "***"


class AssistantReadOnlyGateway:
    """Typed read-only facade with deterministic policy and audit hooks."""

    READ_ROLES = {
        "list_houses": {
            AssistantRole.OWNER,
            AssistantRole.ADMIN,
            AssistantRole.CLEANER,
            AssistantRole.GUEST,
        },
        "check_availability": {AssistantRole.OWNER, AssistantRole.ADMIN, AssistantRole.GUEST},
        "get_price_calendar": {AssistantRole.OWNER, AssistantRole.ADMIN, AssistantRole.GUEST},
        "calculate_stay_total": {AssistantRole.OWNER, AssistantRole.ADMIN, AssistantRole.GUEST},
        "list_booking_summaries": {
            AssistantRole.OWNER,
            AssistantRole.ADMIN,
            AssistantRole.CLEANER,
            AssistantRole.GUEST,
        },
        "get_revenue_summary": {AssistantRole.OWNER, AssistantRole.ADMIN},
    }

    def __init__(
        self,
        boundary: ReadBoundary,
        *,
        enabled: bool = False,
        cursor_secret: str | None = None,
        audit_sink: AuditSink | None = None,
        scope_resolver: ScopeResolver | None = None,
        clock: Clock | None = None,
        cursor_ttl_seconds: int = 300,
    ) -> None:
        if enabled and not cursor_secret:
            raise ValueError("cursor_secret is required when assistant gateway is enabled")
        self._boundary = boundary
        self._enabled = enabled
        self._audit = audit_sink or _NullAuditSink()
        self._scope_resolver = scope_resolver
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._cursor = (
            _CursorCodec(cursor_secret, self._clock, cursor_ttl_seconds)
            if cursor_secret
            else None
        )

    async def list_houses(
        self, context: TrustedContext, args: ListHousesArgs | Mapping[str, Any] | None = None
    ) -> ToolResult[HouseListData]:
        parsed = await self._parse(context, "list_houses", args or {}, ListHousesArgs)
        if isinstance(parsed, ToolResult):
            return parsed
        return await self._call(
            context,
            "list_houses",
            PiiMode.MASKED,
            lambda: self._boundary.list_houses(),
            lambda read: HouseListData(
                items=[
                    HouseView(
                        house_id=house.house_id,
                        name=house.name,
                        capacity=house.capacity,
                        active=house.active,
                    )
                    for house in read.value
                ],
                freshness=_freshness(read, self._clock()),
            ),
            args_digest=_model_digest(parsed),
        )

    async def check_availability(
        self, context: TrustedContext, args: CheckAvailabilityArgs | Mapping[str, Any]
    ) -> ToolResult[AvailabilityData]:
        parsed = await self._parse(context, "check_availability", args, CheckAvailabilityArgs)
        if isinstance(parsed, ToolResult):
            return parsed
        return await self._call(
            context,
            "check_availability",
            PiiMode.MASKED,
            lambda: self._boundary.check_availability(parsed),
            lambda read: AvailabilityData(
                query=parsed.date_range,
                items=[
                    AvailabilityView(
                        house_id=item.house_id,
                        house_name=item.house_name,
                        capacity=item.capacity,
                        available=item.available,
                        price_total=_money(item.price_total),
                        blocked_dates=list(item.blocked_dates),
                        minimum_nights=item.minimum_nights,
                    )
                    for item in read.value
                ],
                freshness=_freshness(read, self._clock()),
            ),
            args_digest=_model_digest(parsed),
        )

    async def get_price_calendar(
        self, context: TrustedContext, args: GetPriceCalendarArgs | Mapping[str, Any]
    ) -> ToolResult[PriceCalendarData]:
        parsed = await self._parse(context, "get_price_calendar", args, GetPriceCalendarArgs)
        if isinstance(parsed, ToolResult):
            return parsed
        return await self._call(
            context,
            "get_price_calendar",
            PiiMode.MASKED,
            lambda: self._boundary.get_price_calendar(parsed),
            lambda read: PriceCalendarData(
                house_id=parsed.house_id,
                days=[
                    PriceDayView(
                        date=item.date,
                        price=_money(item.price),
                        minimum_nights=item.minimum_nights,
                    )
                    for item in read.value
                ],
                freshness=_freshness(read, self._clock()),
            ),
            args_digest=_model_digest(parsed),
        )

    async def calculate_stay_total(
        self, context: TrustedContext, args: CalculateStayTotalArgs | Mapping[str, Any]
    ) -> ToolResult[StayTotalData]:
        parsed = await self._parse(context, "calculate_stay_total", args, CalculateStayTotalArgs)
        if isinstance(parsed, ToolResult):
            return parsed
        return await self._call(
            context,
            "calculate_stay_total",
            PiiMode.MASKED,
            lambda: self._boundary.calculate_stay_total(parsed),
            lambda read: StayTotalData(
                house_id=read.value.house_id,
                nights=len(read.value.nightly_breakdown),
                nightly_breakdown=[
                    NightlyPriceView(
                        date=item.date,
                        price=_money(item.price),
                        discount=_money(item.discount),
                    )
                    for item in read.value.nightly_breakdown
                ],
                discount_total=_money(read.value.discount_total),
                total=_money(read.value.total),
                freshness=_freshness(read, self._clock()),
            ),
            args_digest=_model_digest(parsed),
        )

    async def list_booking_summaries(
        self, context: TrustedContext, args: ListBookingSummariesArgs | Mapping[str, Any]
    ) -> ToolResult[BookingListData]:
        parsed = await self._parse(
            context, "list_booking_summaries", args, ListBookingSummariesArgs
        )
        if isinstance(parsed, ToolResult):
            return parsed
        scope = await self._booking_scope(context)
        if isinstance(scope, ToolResult):
            return scope

        effective_pii = self._effective_pii_mode(context, parsed.pii_mode)
        filter_digest = _filter_digest(parsed)
        offset = 0
        limit = parsed.pagination.limit
        if parsed.pagination.cursor:
            if self._cursor is None:
                return await self._error(
                    context,
                    "list_booking_summaries",
                    "invalid_arguments",
                    "Некорректный курсор.",
                    args_digest=filter_digest,
                )
            decoded = self._cursor.read(parsed.pagination.cursor, context, filter_digest)
            if decoded is None:
                return await self._error(
                    context,
                    "list_booking_summaries",
                    "invalid_arguments",
                    "Некорректный или устаревший курсор.",
                    args_digest=filter_digest,
                )
            offset, limit = decoded

        read_result = await self._invoke(
            context,
            "list_booking_summaries",
            lambda: self._boundary.list_bookings(parsed),
            args_digest=filter_digest,
        )
        if isinstance(read_result, ToolResult):
            return read_result

        try:
            rows = list(read_result.value)
            if scope is not None:
                rows = [row for row in rows if row.booking_id in scope]
            rows.sort(key=lambda row: (row.check_in, row.booking_id))
            page_rows = rows[offset : offset + limit]
            has_more = offset + limit < len(rows)
            next_cursor = (
                self._cursor.issue(context, filter_digest, offset + limit, limit)
                if has_more and self._cursor is not None
                else None
            )
            data = BookingListData(
                items=[self._booking_view(row, effective_pii) for row in page_rows],
                page=PaginationResponse(limit=limit, has_more=has_more, next_cursor=next_cursor),
                freshness=_freshness(read_result, self._clock()),
            )
        except (AttributeError, TypeError, ValueError, ValidationError):
            return await self._error(
                context,
                "list_booking_summaries",
                "internal_error",
                "Получены некорректные данные от бизнес-сервиса.",
                args_digest=filter_digest,
            )
        return await self._finish(
            context,
            "list_booking_summaries",
            effective_pii,
            data,
            len(page_rows),
            args_digest=filter_digest,
        )

    async def get_revenue_summary(
        self, context: TrustedContext, args: RevenueSummaryArgs | Mapping[str, Any]
    ) -> ToolResult[RevenueSummaryData]:
        parsed = await self._parse(context, "get_revenue_summary", args, RevenueSummaryArgs)
        if isinstance(parsed, ToolResult):
            return parsed
        return await self._call(
            context,
            "get_revenue_summary",
            PiiMode.MASKED,
            lambda: self._boundary.get_revenue_summary(parsed),
            lambda read: RevenueSummaryData(
                date_range=parsed.date_range,
                booking_count=read.value.booking_count,
                nights=read.value.nights,
                gross_booked=_money(read.value.gross_booked),
                advance_received=_money(read.value.advance_received),
                remainder_due=_money(read.value.remainder_due),
                commission=_money(read.value.commission),
                cleaning_cost=_money(read.value.cleaning_cost),
                profit_estimate=_money(read.value.profit_estimate),
                occupancy_rate=read.value.occupancy_rate,
                adr=_money(read.value.adr),
                nights_to_target=read.value.nights_to_target,
                calculation_status=read.value.calculation_status,
                freshness=_freshness(read, self._clock()),
            ),
            args_digest=_model_digest(parsed),
        )

    async def reject(
        self,
        context: TrustedContext,
        tool_name: str,
        code: str,
        message_public: str,
        *,
        retryable: bool = False,
        field_errors: list[dict[str, str]] | None = None,
        args_digest: str | None = None,
    ) -> ToolResult[Any]:
        """Return a policy rejection through the same audited result path."""
        return await self._error(
            context,
            tool_name,
            code,
            message_public,
            retryable=retryable,
            field_errors=field_errors,
            args_digest=args_digest,
        )

    async def _parse(
        self,
        context: TrustedContext,
        tool_name: str,
        args: BaseModel | Mapping[str, Any],
        model_type: type[BaseModel],
    ) -> BaseModel | ToolResult[Any]:
        if not self._enabled:
            return await self._error(
                context, tool_name, "assistant_disabled", "Помощник пока отключен."
            )
        if not isinstance(context, TrustedContext):
            return await self._error(
                context,
                tool_name,
                "unauthorized",
                "Не удалось подтвердить пользователя.",
            )
        if context.actor_role not in self.READ_ROLES[tool_name]:
            return await self._error(
                context, tool_name, "forbidden", "Доступ к этому запросу ограничен."
            )
        try:
            return args if isinstance(args, model_type) else model_type.model_validate(args)
        except ValidationError as exc:
            field_errors = [
                {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
                for error in exc.errors()
            ]
            return await self._error(
                context,
                tool_name,
                "invalid_arguments",
                "Параметры запроса не прошли проверку.",
                field_errors=field_errors,
                args_digest=_input_digest(args),
            )

    async def _booking_scope(
        self, context: TrustedContext
    ) -> Optional[set[int]] | ToolResult[Any]:
        if context.actor_role in {AssistantRole.OWNER, AssistantRole.ADMIN}:
            return None
        if self._scope_resolver is None:
            return await self._error(
                context,
                "list_booking_summaries",
                "forbidden",
                "Для этой роли доступна только привязанная бронь.",
            )
        try:
            resolved = await self._scope_resolver(context)
            if resolved is None:
                return await self._error(
                    context,
                    "list_booking_summaries",
                    "forbidden",
                    "Для этой роли область доступа не подтверждена.",
                )
            return set(resolved)
        except Exception:
            return await self._error(
                context,
                "list_booking_summaries",
                "internal_error",
                "Не удалось определить область доступа.",
            )

    @staticmethod
    def _effective_pii_mode(context: TrustedContext, requested: PiiMode) -> PiiMode:
        if requested == PiiMode.FULL and context.actor_role in {
            AssistantRole.OWNER,
            AssistantRole.ADMIN,
        }:
            return PiiMode.FULL
        return PiiMode.MASKED

    @staticmethod
    def _booking_view(row: BookingRecord, pii_mode: PiiMode) -> BookingSummaryView:
        status = BookingStatus(row.status)
        source = BookingSource(row.source)
        total = Decimal(str(row.total_price))
        advance = Decimal(str(row.advance_amount))
        remainder = max(Decimal("0"), total - advance)
        full = pii_mode == PiiMode.FULL
        return BookingSummaryView(
            booking_id=row.booking_id,
            house_id=row.house_id,
            house_name=row.house_name,
            check_in=row.check_in,
            check_out=row.check_out,
            nights=(row.check_out - row.check_in).days,
            guests_count=row.guests_count,
            status=status,
            source=source,
            guest_name=row.guest_name if full else _mask_name(row.guest_name),
            guest_phone=row.guest_phone if full else _mask_phone(row.guest_phone),
            total_price=_money(total),
            advance_received=_money(advance),
            remainder_due=_money(remainder),
            commission=_money(row.commission) if full else None,
            pii_mode=pii_mode,
        )

    async def _call(
        self,
        context: TrustedContext,
        tool_name: str,
        pii_mode: PiiMode,
        invoke: Callable[[], Awaitable[BoundaryRead[Any]]],
        render: Callable[[BoundaryRead[Any]], BaseModel],
        *,
        args_digest: str | None = None,
    ) -> ToolResult[Any]:
        read_result = await self._invoke(
            context, tool_name, invoke, args_digest=args_digest
        )
        if isinstance(read_result, ToolResult):
            return read_result
        try:
            data = render(read_result)
        except (AttributeError, TypeError, ValueError, ValidationError):
            return await self._error(
                context,
                tool_name,
                "internal_error",
                "Получены некорректные данные от бизнес-сервиса.",
                args_digest=args_digest,
            )
        count = len(data.items) if hasattr(data, "items") else None
        return await self._finish(
            context,
            tool_name,
            pii_mode,
            data,
            count,
            args_digest=args_digest,
        )

    async def _invoke(
        self,
        context: TrustedContext,
        tool_name: str,
        invoke: Callable[[], Awaitable[BoundaryRead[Any]]],
        *,
        args_digest: str | None = None,
    ) -> BoundaryRead[Any] | ToolResult[Any]:
        try:
            read_result = await invoke()
            if not isinstance(read_result, BoundaryRead):
                return await self._error(
                    context,
                    tool_name,
                    "internal_error",
                    "Бизнес-сервис вернул некорректный ответ.",
                    args_digest=args_digest,
                )
            return read_result
        except BoundaryError as exc:
            return await self._error(
                context,
                tool_name,
                exc.code,
                exc.message_public,
                retryable=exc.retryable,
                args_digest=args_digest,
            )
        except TimeoutError:
            return await self._error(
                context,
                tool_name,
                "upstream_timeout",
                "Не удалось получить актуальные данные. Повторите запрос.",
                retryable=True,
                args_digest=args_digest,
            )
        except ConnectionError:
            return await self._error(
                context,
                tool_name,
                "upstream_unavailable",
                "Сервис бронирований временно недоступен.",
                retryable=True,
                args_digest=args_digest,
            )
        except Exception:
            return await self._error(
                context,
                tool_name,
                "internal_error",
                "Не удалось обработать запрос.",
                args_digest=args_digest,
            )

    async def _finish(
        self,
        context: TrustedContext,
        tool_name: str,
        pii_mode: PiiMode,
        data: BaseModel,
        result_count: int | None,
        *,
        args_digest: str | None = None,
    ) -> ToolResult[Any]:
        result = ToolResult(request_id=context.request_id, data=data)
        await self._audit_event(
            context,
            tool_name,
            pii_mode,
            "success",
            result_count=result_count,
            args_digest=args_digest,
        )
        return result

    async def _error(
        self,
        context: TrustedContext,
        tool_name: str,
        code: str,
        message_public: str,
        *,
        retryable: bool = False,
        field_errors: list[dict[str, str]] | None = None,
        args_digest: str | None = None,
    ) -> ToolResult[Any]:
        request_id = getattr(context, "request_id", uuid4())
        if not isinstance(request_id, UUID):
            request_id = uuid4()
        try:
            error = ToolError(
                code=code,
                message_public=message_public,
                retryable=retryable,
                request_id=request_id,
                field_errors=field_errors or [],
            )
        except ValidationError:
            error = ToolError(
                code="internal_error",
                message_public="Не удалось обработать запрос.",
                retryable=False,
                request_id=request_id,
            )
            code = "internal_error"
        if isinstance(context, TrustedContext):
            outcome = (
                "denied"
                if code in {"assistant_disabled", "unauthorized", "forbidden"}
                else "error"
            )
            await self._audit_event(
                context,
                tool_name,
                PiiMode.MASKED,
                outcome,
                error_code=code,
                args_digest=args_digest,
            )
        return ToolResult(request_id=request_id, error=error)

    async def _audit_event(
        self,
        context: TrustedContext,
        tool_name: str,
        pii_mode: PiiMode,
        outcome: str,
        *,
        result_count: int | None = None,
        error_code: str | None = None,
        args_digest: str | None = None,
    ) -> None:
        event = AuditEvent(
            event_id=uuid4(),
            request_id=context.request_id,
            session_id=context.session_id,
            actor_telegram_id=context.actor_telegram_id,
            actor_role=context.actor_role,
            tool_name=tool_name,
            outcome=outcome,
            created_at=self._clock(),
            args_digest=args_digest or hashlib.sha256(tool_name.encode("utf-8")).hexdigest(),
            pii_mode=pii_mode,
            result_count=result_count,
            error_code=error_code,
        )
        try:
            await self._audit.record(event)
        except Exception:
            # Observability must not turn a read-only answer into a second failure.
            return None
