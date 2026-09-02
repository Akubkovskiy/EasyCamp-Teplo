"""Disabled-by-default assistant boundary.

The package is intentionally not imported by the application entrypoint yet.
It provides a typed, read-only seam for a later owner-only runtime.
"""

from app.assistant.contracts import (
    AssistantRole,
    BookingSource,
    BookingStatus,
    CalculateStayTotalArgs,
    CheckAvailabilityArgs,
    DateRange,
    GetPriceCalendarArgs,
    ListBookingSummariesArgs,
    ListHousesArgs,
    PiiMode,
    RevenueSummaryArgs,
    TrustedContext,
)
from app.assistant.gateway import (
    AssistantReadOnlyGateway,
    BoundaryRead,
    InMemoryAuditSink,
    ReadBoundary,
)

__all__ = [
    "AssistantReadOnlyGateway",
    "AssistantRole",
    "BookingSource",
    "BookingStatus",
    "BoundaryRead",
    "CalculateStayTotalArgs",
    "CheckAvailabilityArgs",
    "DateRange",
    "GetPriceCalendarArgs",
    "InMemoryAuditSink",
    "ListBookingSummariesArgs",
    "ListHousesArgs",
    "PiiMode",
    "ReadBoundary",
    "RevenueSummaryArgs",
    "TrustedContext",
]
