from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.assistant.ask import AssistantAskTransport
from app.assistant.contracts import AssistantRole, TrustedContext
from app.assistant.gateway import (
    AssistantReadOnlyGateway,
    AvailabilityRecord,
    BoundaryRead,
    HouseRecord,
)


NOW = datetime(2026, 9, 2, 12, tzinfo=timezone.utc)


def context(role=AssistantRole.OWNER, session_id="owner-session"):
    return TrustedContext(
        request_id=uuid4(),
        session_id=session_id,
        actor_telegram_id=111,
        actor_role=role,
    )


class Boundary:
    def __init__(self):
        self.calls = []

    def read(self, value):
        return BoundaryRead(value=value, as_of=NOW, stale_after_seconds=60)

    async def list_houses(self):
        self.calls.append("list_houses")
        return self.read([HouseRecord(1, "Дом 1", 4)])

    async def check_availability(self, args):
        self.calls.append("check_availability")
        return self.read([AvailabilityRecord(1, "Дом 1", 4, True, 10000)])

    async def get_price_calendar(self, args):
        self.calls.append("get_price_calendar")
        return self.read([])

    async def calculate_stay_total(self, args):
        self.calls.append("calculate_stay_total")
        return self.read(SimpleNamespace())

    async def list_bookings(self, args):
        self.calls.append("list_bookings")
        return self.read([])

    async def get_revenue_summary(self, args):
        self.calls.append("get_revenue_summary")
        return self.read(SimpleNamespace())


@pytest.fixture
def components():
    boundary = Boundary()
    gateway = AssistantReadOnlyGateway(
        boundary,
        enabled=True,
        cursor_secret="unit-test-secret",
        clock=lambda: NOW,
    )
    return boundary, gateway


def request(session_id="owner-session", **arguments):
    return {
        "session_id": session_id,
        "query": {
            "intent": "check_availability",
            "arguments": arguments,
        },
    }


@pytest.mark.asyncio
async def test_disabled_transport_returns_explicit_state_without_gateway_call(components):
    boundary, gateway = components
    transport = AssistantAskTransport(gateway)

    result = await transport.handle(
        context(),
        {"garbage": "ignored"},
    )

    assert result.error.code == "assistant_disabled"
    assert boundary.calls == []


@pytest.mark.asyncio
async def test_enabled_transport_requires_owner_and_verified_matching_session(components):
    boundary, gateway = components
    transport = AssistantAskTransport(
        gateway,
        enabled=True,
        session_verifier=lambda _context: _verified(True),
    )

    result = await transport.handle(
        context(),
        request(date_range={"start": "2026-09-12", "end": "2026-09-15"}),
    )
    assert result.ok
    assert boundary.calls == ["check_availability"]

    admin = await transport.handle(
        context(AssistantRole.ADMIN),
        request(date_range={"start": "2026-09-12", "end": "2026-09-15"}),
    )
    assert admin.error.code == "forbidden"
    assert boundary.calls == ["check_availability"]

    mismatch = await transport.handle(
        context(session_id="other-session"),
        request(date_range={"start": "2026-09-12", "end": "2026-09-15"}),
    )
    assert mismatch.error.code == "unauthorized"
    assert boundary.calls == ["check_availability"]


async def _verified(value):
    return value


@pytest.mark.asyncio
async def test_structured_arguments_are_strict_and_invalid_request_does_not_call_boundary(
    components,
):
    boundary, gateway = components
    transport = AssistantAskTransport(
        gateway,
        enabled=True,
        session_verifier=lambda _context: _verified(True),
    )

    missing = await transport.handle(context(), request())
    assert missing.error.code == "invalid_arguments"

    extra = await transport.handle(
        context(),
        {
            "session_id": "owner-session",
            "extra": "forbidden",
            "query": {"intent": "check_availability", "arguments": {}},
        },
    )
    assert extra.error.code == "invalid_arguments"
    assert boundary.calls == []


@pytest.mark.asyncio
async def test_failed_verifier_and_unknown_intent_fail_closed(components):
    boundary, gateway = components
    transport = AssistantAskTransport(
        gateway,
        enabled=True,
        session_verifier=lambda _context: _verified(False),
    )
    denied = await transport.handle(
        context(),
        request(date_range={"start": "2026-09-12", "end": "2026-09-15"}),
    )
    assert denied.error.code == "unauthorized"

    trusted = AssistantAskTransport(
        gateway,
        enabled=True,
        session_verifier=lambda _context: _verified(True),
    )
    unknown = await trusted.handle(
        context(),
        {
            "session_id": "owner-session",
            "query": {"intent": "create_booking", "arguments": {}},
        },
    )
    assert unknown.error.code == "invalid_arguments"
    assert boundary.calls == []


def test_enabled_transport_requires_a_session_verifier(components):
    _boundary, gateway = components
    with pytest.raises(ValueError):
        AssistantAskTransport(gateway, enabled=True)
