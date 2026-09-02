"""Liveness and database-aware readiness endpoints."""

from fastapi import APIRouter, Response, status

from app.core.config import settings
from app.services.readiness_service import (
    REQUIRED_BOOKING_INDEX,
    check_database_readiness,
)

router = APIRouter()


@router.get("/health", tags=["system"])
async def healthcheck():
    """Process liveness only; this endpoint intentionally does not touch state."""

    return {"status": "ok"}


@router.get("/ready", tags=["system"])
async def readiness(response: Response):
    """Report whether this process can safely serve the current booking schema."""

    if settings.restore_maintenance_mode:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "reason": "restore_maintenance_mode"}

    database_readiness = await check_database_readiness()
    if not database_readiness.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        payload = {
            "status": "not_ready",
            "reason": database_readiness.reason,
        }
        if database_readiness.missing_tables:
            payload["missing_tables"] = list(database_readiness.missing_tables)
        if database_readiness.missing_columns:
            payload["missing_columns"] = list(database_readiness.missing_columns)
        if database_readiness.missing_index:
            payload["missing_index"] = database_readiness.missing_index
        return payload

    return {
        "status": "ready",
        "database": "ok",
        "booking_identity_index": REQUIRED_BOOKING_INDEX,
    }
