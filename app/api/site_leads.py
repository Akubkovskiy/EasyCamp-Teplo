"""Site lead intake endpoint (Phase S10.1).

Принимает заявки с публичного сайта `teplo-v-arkhyze.ru`. Создаёт
`Booking(status=NEW, source=DIRECT)` в источнике правды (EasyCamp DB)
и шлёт админам Telegram-уведомление с inline-кнопками для подтверждения.

Защита: header `X-Site-Token` должен совпадать с `settings.site_lead_token`.
Если token не задан в окружении — endpoint полностью отключён (503),
чтобы случайный публичный POST не создал бронь.

Идемпотентность: если в payload передан `external_ref`, повторный POST
с тем же значением вернёт ту же бронь (по `Booking.external_id`).
"""
import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import AsyncSessionLocal
from app.models import Booking, BookingSource, BookingStatus
from app.schemas.booking import BookingCreate
from app.services.booking_service import BookingService
from app.services.notification_service import send_safe

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["site"])


# -------------------------------------------------
# Schemas
# -------------------------------------------------


class SiteLeadCreate(BaseModel):
    """Заявка с сайта. Минимальный набор полей чтобы создать `Booking`."""

    guest_name: str = Field(min_length=2, max_length=120)
    guest_phone: str = Field(min_length=10, max_length=32)
    check_in: date
    check_out: date
    guests_count: int = Field(default=2, ge=1, le=20)
    house_id: Optional[int] = None
    house_name: Optional[str] = Field(default=None, max_length=120)
    comment: str = Field(default="", max_length=2000)
    source: str = Field(default="website", max_length=64)
    external_ref: Optional[str] = Field(default=None, max_length=64)

    @field_validator("check_out")
    @classmethod
    def validate_dates(cls, v: date, info):
        ci = info.data.get("check_in")
        if ci and v <= ci:
            raise ValueError("check_out must be after check_in")
        return v


class SiteLeadOut(BaseModel):
    """Ответ для site API. lead_id == Booking.id."""

    lead_id: int
    booking_id: int
    status: str
    house_id: Optional[int]
    duplicate: bool = False  # True если возвращён существующий booking


# -------------------------------------------------
# Dependencies
# -------------------------------------------------


async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


def require_site_token(x_site_token: str | None = Header(default=None)) -> None:
    """Авторизация по статичному токену. Если в окружении токен пуст —
    endpoint считается отключённым (503), чтобы избежать случайного
    публичного создания броней без auth."""
    expected = (settings.site_lead_token or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Site lead intake disabled (SITE_LEAD_TOKEN not set)",
        )
    provided = (x_site_token or "").strip()
    if not provided or provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing site token",
        )


# -------------------------------------------------
# Notification (best-effort, не валит создание брони)
# -------------------------------------------------


async def _notify_admins(booking: Booking, source: str, comment: str | None) -> None:
    try:
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        from app.models import UserRole
        from app.telegram.auth.admin import get_all_users
        from app.telegram.bot import bot

        users = await get_all_users()
        admin_ids = {
            u.telegram_id
            for u in users
            if u.role in {UserRole.ADMIN, UserRole.OWNER} and u.telegram_id
        }
        admin_ids.add(settings.telegram_chat_id)

        nights = (booking.check_out - booking.check_in).days
        text = (
            "🌐 <b>Новая заявка с сайта</b>\n\n"
            f"#{booking.id} · house_id={booking.house_id}\n"
            f"📅 {booking.check_in.strftime('%d.%m.%Y')} — "
            f"{booking.check_out.strftime('%d.%m.%Y')} ({nights} сут.)\n"
            f"👥 {booking.guests_count}\n"
            f"💰 {int(booking.total_price):,} ₽\n\n"
            f"Гость: {booking.guest_name} ({booking.guest_phone})\n"
            f"Источник: <code>{source}</code>"
        )
        if comment:
            text += f"\nКомментарий: {comment[:500]}"

        kb = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"site_lead:confirm:{booking.id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"site_lead:reject:{booking.id}",
                ),
            ]]
        )

        for aid in admin_ids:
            await send_safe(bot, aid, text, reply_markup=kb, context=f"site_lead admin={aid}")
    except Exception as e:
        logger.error(f"site_lead admin notify failed: {e}", exc_info=True)


# -------------------------------------------------
# POST /api/leads
# -------------------------------------------------


@router.post(
    "/leads",
    response_model=SiteLeadOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_site_token)],
)
async def create_site_lead(
    payload: SiteLeadCreate,
    session: AsyncSession = Depends(get_async_session),
) -> SiteLeadOut:
    # A numeric EasyCamp house_id is the stable cross-system identity. Names are
    # display metadata only: fuzzy/name fallback can silently assign a real lead
    # to the wrong house after a rename or typo.
    if payload.house_id is None:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "missing_house_id",
                "message": "house_id is required; house_name is not a stable booking identity",
            },
        )

    ext_id = f"site:{payload.external_ref}" if payload.external_ref else None

    comment_parts: list[str] = []
    if payload.comment:
        comment_parts.append(payload.comment.strip())
    if payload.source and payload.source != "website":
        comment_parts.append(f"[source: {payload.source}]")
    full_comment = " | ".join(comment_parts) if comment_parts else None

    # The service owns idempotency, final overlap validation and insertion in a
    # single serialized SQLite transaction.
    create = BookingCreate(
        house_id=payload.house_id,
        guest_name=payload.guest_name.strip(),
        guest_phone=payload.guest_phone.strip(),
        check_in=payload.check_in,
        check_out=payload.check_out,
        guests_count=payload.guests_count,
        total_price=Decimal("0"),
        advance_amount=Decimal("0"),
        commission=Decimal("0"),
        prepayment_owner=Decimal("0"),
        status=BookingStatus.NEW,
        source=BookingSource.DIRECT,
        external_id=ext_id,
    )
    result = await BookingService.create_booking_result(session, create)
    if result.duplicate and result.booking:
        existing = result.booking
        return SiteLeadOut(
            lead_id=existing.id,
            booking_id=existing.id,
            status=existing.status.value,
            house_id=existing.house_id,
            duplicate=True,
        )

    if not result.booking:
        if result.reason == "unknown_house":
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "unknown_house_id",
                    "message": f"No EasyCamp house exists with house_id={payload.house_id}",
                },
            )
        if result.reason == "unavailable":
            raise HTTPException(
                status_code=409,
                detail="Cannot create booking — dates are not available",
            )
        raise HTTPException(
            status_code=500,
            detail="Booking creation failed safely; no booking was written",
        )

    booking = result.booking

    # Telegram notify is best-effort and happens only for a genuinely new row.
    await _notify_admins(booking, payload.source, full_comment)

    return SiteLeadOut(
        lead_id=booking.id,
        booking_id=booking.id,
        status=booking.status.value,
        house_id=booking.house_id,
        duplicate=False,
    )
