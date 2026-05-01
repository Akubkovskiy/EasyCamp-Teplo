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
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import AsyncSessionLocal
from app.models import Booking, BookingSource, BookingStatus, House
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
# House resolution
# -------------------------------------------------


async def _resolve_house_id(
    session: AsyncSession,
    *,
    explicit_id: int | None,
    explicit_name: str | None,
) -> tuple[int | None, str | None]:
    """Возвращает (house_id, fallback_note). Стратегия:
    1. Явный id — берём, если House существует.
    2. Имя — пробуем точное совпадение, потом ILIKE %x%.
    3. Иначе — fallback на первый House. Возвращаем note для аудита.
    """
    if explicit_id:
        h = await session.get(House, explicit_id)
        if h:
            return h.id, None

    if explicit_name:
        # exact
        q = await session.execute(
            select(House).where(House.name == explicit_name)
        )
        h = q.scalar_one_or_none()
        if h:
            return h.id, None
        # fuzzy ILIKE
        like = f"%{explicit_name}%"
        q = await session.execute(
            select(House).where(House.name.ilike(like)).limit(1)
        )
        h = q.scalar_one_or_none()
        if h:
            return h.id, f"fuzzy match by name: '{explicit_name}'"

    # fallback: первый по id
    q = await session.execute(select(House).order_by(House.id).limit(1))
    fallback = q.scalar_one_or_none()
    if fallback:
        return fallback.id, (
            f"fallback to first house (requested id={explicit_id}, "
            f"name='{explicit_name}')"
        )
    return None, "no houses in database"


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
    # 1) Идемпотентность по external_ref
    if payload.external_ref:
        ext_id = f"site:{payload.external_ref}"
        q = await session.execute(
            select(Booking).where(
                Booking.external_id == ext_id,
                Booking.source == BookingSource.DIRECT,
            )
        )
        existing = q.scalar_one_or_none()
        if existing:
            return SiteLeadOut(
                lead_id=existing.id,
                booking_id=existing.id,
                status=existing.status.value,
                house_id=existing.house_id,
                duplicate=True,
            )
    else:
        ext_id = None

    # 2) Резолвим house
    house_id, fallback_note = await _resolve_house_id(
        session,
        explicit_id=payload.house_id,
        explicit_name=payload.house_name,
    )
    if not house_id:
        raise HTTPException(
            status_code=422,
            detail="Cannot resolve house: no houses in database",
        )

    comment_parts: list[str] = []
    if payload.comment:
        comment_parts.append(payload.comment.strip())
    if fallback_note:
        comment_parts.append(f"[house resolution: {fallback_note}]")
    if payload.source and payload.source != "website":
        comment_parts.append(f"[source: {payload.source}]")
    full_comment = " | ".join(comment_parts) if comment_parts else None

    # 3) Создаём бронь через сервис (overlap guard внутри)
    create = BookingCreate(
        house_id=house_id,
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
    )
    booking = await BookingService.create_booking(session, create)
    if not booking:
        raise HTTPException(
            status_code=409,
            detail="Cannot create booking — dates are not available",
        )

    # external_id вешаем после успешного create — чтобы повторный POST
    # увидел эту бронь как идемпотентную.
    if ext_id:
        booking.external_id = ext_id
        booking.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(booking)

    # 4) Telegram notify (best-effort, не валит ответ)
    await _notify_admins(booking, payload.source, full_comment)

    return SiteLeadOut(
        lead_id=booking.id,
        booking_id=booking.id,
        status=booking.status.value,
        house_id=booking.house_id,
        duplicate=False,
    )
