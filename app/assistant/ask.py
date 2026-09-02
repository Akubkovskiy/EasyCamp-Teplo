"""Internal owner-only ``/ask`` transport for structured read queries.

This is intentionally a transport-neutral handler, not a FastAPI router or a
Telegram handler. It is safe to import and remains disabled unless both the
transport and the injected typed gateway are explicitly enabled later.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Protocol, runtime_checkable
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.assistant.contracts import AssistantRole, ToolError, TrustedContext
from app.assistant.gateway import AssistantReadOnlyGateway, ToolResult


class AskIntent(str, Enum):
    LIST_HOUSES = "list_houses"
    CHECK_AVAILABILITY = "check_availability"
    GET_PRICE_CALENDAR = "get_price_calendar"
    CALCULATE_STAY_TOTAL = "calculate_stay_total"
    LIST_BOOKING_SUMMARIES = "list_booking_summaries"
    GET_REVENUE_SUMMARY = "get_revenue_summary"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AskQuery(_StrictModel):
    intent: AskIntent
    arguments: dict[str, Any] = Field(default_factory=dict, max_length=32)


class AskRequest(_StrictModel):
    """Structured query envelope; it contains no actor-controlled identity."""

    session_id: str = Field(min_length=1, max_length=128)
    query: AskQuery


SessionVerifier = Callable[[TrustedContext], Awaitable[bool]]
ASSISTANT_READ_SCOPE = "assistant:read"


@dataclass(frozen=True)
class TelegramActor:
    """Telegram identity supplied by the aiogram/runtime transport."""

    telegram_id: int

    def __post_init__(self) -> None:
        if isinstance(self.telegram_id, bool) or not isinstance(self.telegram_id, int):
            raise TypeError("telegram_id must be a positive integer")
        if self.telegram_id <= 0:
            raise ValueError("telegram_id must be a positive integer")


class TrustedSession(_StrictModel):
    """Server-issued session bound to one Telegram actor and explicit scopes."""

    session_id: str = Field(min_length=1, max_length=128)
    actor_telegram_id: int = Field(gt=0)
    actor_role: AssistantRole
    scopes: set[str] = Field(min_length=1, max_length=16)
    issued_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_lifetime(self) -> TrustedSession:
        if self.issued_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("session timestamps must include a timezone")
        if self.expires_at <= self.issued_at:
            raise ValueError("session must expire after it is issued")
        return self


@runtime_checkable
class TrustedSessionResolver(Protocol):
    """Server-side lookup for an active session; it must not trust request data."""

    async def resolve(self, session_id: str) -> TrustedSession | None: ...


class AssistantAskTransport:
    """Owner-only internal transport over ``AssistantReadOnlyGateway``."""

    INTENT_METHODS: ClassVar[dict[AskIntent, str]] = {
        AskIntent.LIST_HOUSES: "list_houses",
        AskIntent.CHECK_AVAILABILITY: "check_availability",
        AskIntent.GET_PRICE_CALENDAR: "get_price_calendar",
        AskIntent.CALCULATE_STAY_TOTAL: "calculate_stay_total",
        AskIntent.LIST_BOOKING_SUMMARIES: "list_booking_summaries",
        AskIntent.GET_REVENUE_SUMMARY: "get_revenue_summary",
    }

    def __init__(
        self,
        gateway: AssistantReadOnlyGateway,
        *,
        enabled: bool = False,
        session_verifier: SessionVerifier | None = None,
    ) -> None:
        if enabled and session_verifier is None:
            raise ValueError("session_verifier is required when /ask transport is enabled")
        self._gateway = gateway
        self._enabled = enabled
        self._session_verifier = session_verifier

    @property
    def enabled(self) -> bool:
        """Expose the feature flag to a pre-auth transport without mutable state."""
        return self._enabled

    async def handle(
        self,
        context: TrustedContext,
        request: AskRequest | Mapping[str, Any],
    ) -> ToolResult[Any]:
        if not isinstance(context, TrustedContext):
            return _standalone_error("unauthorized", "Не удалось подтвердить пользователя.")

        if not self._enabled:
            return await self._gateway.reject(
                context,
                "/ask",
                "assistant_disabled",
                "Помощник пока отключен.",
            )

        parsed, field_errors = self._parse_request(request)
        if parsed is None:
            return await self._gateway.reject(
                context,
                "/ask",
                "invalid_arguments",
                "Структура /ask-запроса не прошла проверку.",
                field_errors=field_errors,
            )
        if parsed.session_id != context.session_id:
            return await self._gateway.reject(
                context,
                "/ask",
                "unauthorized",
                "Сессия запроса не совпадает с trusted-сессией.",
            )
        if context.actor_role != AssistantRole.OWNER:
            return await self._gateway.reject(
                context,
                "/ask",
                "forbidden",
                "Доступ к помощнику ограничен владельцем.",
            )
        verifier = self._session_verifier
        if verifier is None:
            return await self._gateway.reject(
                context,
                "/ask",
                "unauthorized",
                "Trusted-сессия не подтверждена.",
            )
        try:
            verified = await verifier(context)
        except Exception:  # noqa: BLE001 - an injected verifier must fail closed
            verified = False
        if not verified:
            return await self._gateway.reject(
                context,
                "/ask",
                "unauthorized",
                "Trusted-сессия не подтверждена.",
            )

        method_name = self.INTENT_METHODS.get(parsed.query.intent)
        if method_name is None:
            return await self._gateway.reject(
                context,
                "/ask",
                "invalid_arguments",
                "Такой structured intent пока не поддерживается.",
            )
        method = getattr(self._gateway, method_name)
        return await method(context, parsed.query.arguments)

    @staticmethod
    def _parse_request(
        request: AskRequest | Mapping[str, Any],
    ) -> tuple[AskRequest | None, list[dict[str, str]]]:
        try:
            parsed = (
                request
                if isinstance(request, AskRequest)
                else AskRequest.model_validate(request)
            )
            return parsed, []
        except ValidationError as exc:
            field_errors = [
                {
                    "field": ".".join(str(part) for part in error["loc"]),
                    "message": error["msg"],
                }
                for error in exc.errors()
            ]
            return None, field_errors


class TelegramTrustedAskAdapter:
    """Bind a Telegram actor and server session before entering ``/ask``.

    This is an integration boundary, not a Telegram handler. The caller must
    obtain ``TelegramActor`` from the trusted aiogram update and provide a
    server-side ``TrustedSessionResolver``. No actor identity is accepted from
    the model or from the structured request body.
    """

    def __init__(
        self,
        transport: AssistantAskTransport,
        session_resolver: TrustedSessionResolver,
        *,
        required_scope: str = ASSISTANT_READ_SCOPE,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(required_scope, str) or not required_scope.strip():
            raise ValueError("required_scope must be a non-empty string")
        self._transport = transport
        self._session_resolver = session_resolver
        self._required_scope = required_scope
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def handle(
        self,
        actor: TelegramActor,
        request: AskRequest | Mapping[str, Any],
    ) -> ToolResult[Any]:
        if not isinstance(actor, TelegramActor):
            return _standalone_error("unauthorized", "Не удалось подтвердить пользователя.")

        if not self._transport.enabled:
            return _standalone_error("assistant_disabled", "Помощник пока отключен.")

        parsed, field_errors = AssistantAskTransport._parse_request(request)
        if parsed is None:
            return _standalone_error(
                "invalid_arguments",
                "Структура /ask-запроса не прошла проверку.",
                field_errors=field_errors,
            )

        try:
            session = await self._session_resolver.resolve(parsed.session_id)
        except Exception:  # noqa: BLE001 - an unavailable session store fails closed
            return _standalone_error(
                "upstream_unavailable",
                "Не удалось проверить trusted-сессию. Повторите запрос.",
                retryable=True,
            )

        if not isinstance(session, TrustedSession):
            return _standalone_error("unauthorized", "Trusted-сессия не подтверждена.")
        if session.session_id != parsed.session_id:
            return _standalone_error("unauthorized", "Trusted-сессия не подтверждена.")
        if session.actor_telegram_id != actor.telegram_id:
            return _standalone_error(
                "unauthorized",
                "Сессия не принадлежит этому Telegram-пользователю.",
            )

        now = self._clock()
        if now.tzinfo is None or now < session.issued_at or now >= session.expires_at:
            return _standalone_error("unauthorized", "Trusted-сессия истекла или недействительна.")
        if self._required_scope not in session.scopes:
            return _standalone_error("forbidden", "У сессии нет требуемой области доступа.")
        if session.actor_role != AssistantRole.OWNER:
            return _standalone_error("forbidden", "Доступ к помощнику ограничен владельцем.")

        context = TrustedContext(
            request_id=uuid4(),
            session_id=session.session_id,
            actor_telegram_id=actor.telegram_id,
            actor_role=session.actor_role,
        )
        return await self._transport.handle(context, parsed)


def _standalone_error(
    code: str,
    message_public: str,
    *,
    retryable: bool = False,
    field_errors: list[dict[str, str]] | None = None,
) -> ToolResult[Any]:
    request_id = uuid4()
    return ToolResult(
        request_id=request_id,
        error=ToolError(
            code=code,
            message_public=message_public,
            retryable=retryable,
            request_id=request_id,
            field_errors=field_errors or [],
        ),
    )
