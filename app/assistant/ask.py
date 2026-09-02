"""Internal owner-only ``/ask`` transport for structured read queries.

This is intentionally a transport-neutral handler, not a FastAPI router or a
Telegram handler. It is safe to import and remains disabled unless both the
transport and the injected typed gateway are explicitly enabled later.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Awaitable, Callable, Mapping
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

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


class AssistantAskTransport:
    """Owner-only internal transport over ``AssistantReadOnlyGateway``."""

    INTENT_METHODS = {
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
        except Exception:
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


def _standalone_error(code: str, message_public: str) -> ToolResult[Any]:
    request_id = uuid4()
    return ToolResult(
        request_id=request_id,
        error=ToolError(
            code=code,
            message_public=message_public,
            retryable=False,
            request_id=request_id,
        ),
    )
