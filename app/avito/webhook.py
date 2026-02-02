"""
Avito webhook handler with signature verification and idempotency.

Modes (via AVITO_WEBHOOK_MODE env var):
- "off": No signature verification (backward compatible)
- "warn": Log warning on invalid/missing signature, but allow request
- "enforce": Reject (401) on invalid signature if secret is configured

If AVITO_WEBHOOK_SECRET is empty, behaves as "off" regardless of mode.
"""
import logging
import hmac
import hashlib
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter(prefix="/avito", tags=["avito"])
logger = logging.getLogger(__name__)


def verify_signature(body: bytes, signature: str) -> bool:
    """
    Verify HMAC-SHA256 signature.
    Returns True if signature is valid OR if no secret is configured.
    """
    if not settings.avito_webhook_secret:
        return True  # No secret configured, skip verification
    
    expected = hmac.new(
        settings.avito_webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


@router.post("/webhook")
async def avito_webhook(request: Request):
    """
    Handle Avito webhook with optional signature verification and idempotency.
    
    Signature verification modes:
    - off: Accept all requests (default, backward compatible)
    - warn: Log warning on invalid signature but accept
    - enforce: Reject invalid signature with 401
    """
    # Get raw body for signature verification (before Pydantic parsing)
    body = await request.body()
    
    # Signature verification based on mode
    mode = settings.avito_webhook_mode
    secret_configured = bool(settings.avito_webhook_secret)
    
    if mode != "off" and secret_configured:
        signature = request.headers.get("X-Avito-Signature", "")
        is_valid = verify_signature(body, signature)
        
        if not is_valid:
            if mode == "enforce":
                logger.warning(
                    "Webhook signature verification FAILED (enforce mode) - rejecting request"
                )
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid signature"}
                )
            else:  # mode == "warn"
                logger.warning(
                    "Webhook signature verification FAILED (warn mode) - allowing request"
                )
    
    # Parse event from raw body
    try:
        event_data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse webhook payload as JSON: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON payload"}
        )
    
    event_type = event_data.get("event_type", "unknown")
    payload = event_data.get("payload", {})
    
    logger.info("Received Avito webhook: %s", event_type)
    
    # Process booking webhook
    try:
        from app.avito.schemas import AvitoWebhookEvent, AvitoBookingPayload
        from app.database import AsyncSessionLocal
        from app.services.booking_service import create_or_update_avito_booking
        from app.telegram.notifier import notify_new_avito_event
        from app.models import Booking, BookingSource
        from sqlalchemy import select
        
        # Parse full event for notification
        event = AvitoWebhookEvent(**event_data)
        
        # Parse booking payload
        booking_payload = AvitoBookingPayload(**payload)
        avito_id = str(booking_payload.avito_booking_id)
        
        async with AsyncSessionLocal() as session:
            # === IDEMPOTENCY CHECK ===
            # Check if this Avito booking already exists
            stmt = select(Booking).where(
                Booking.external_id == avito_id,
                Booking.source == BookingSource.AVITO
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.info(f"Webhook already processed for Avito booking {avito_id} (DB ID: {existing.id})")
                return {
                    "status": "already_processed",
                    "booking_id": existing.id
                }
            
            # Create new booking
            booking = await create_or_update_avito_booking(session, booking_payload)
        
        # Notify about new event
        await notify_new_avito_event(event, request, booking)
        
        return {
            "status": "ok",
            "booking_id": booking.id if booking else None
        }
        
    except Exception as e:
        logger.error("Error processing Avito webhook: %s", e, exc_info=True)
        # Return 200 to prevent infinite retries from Avito
        # The error is logged for investigation
        return {
            "status": "error",
            "message": str(e)
        }
