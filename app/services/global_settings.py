"""Тонкий хелпер чтения/записи `GlobalSetting` с типизацией.

Используется guest-flow и админкой для опций, которые должны быть
конфигурируемы без перезапуска бота:
- `guest_cancel_window_days` (int) — за сколько дней до заезда гость
  может отменить бронь сам. Default: 7.
- `guest_instruction_open_hours` (int) — за сколько часов до заезда
  открывается инструкция по заселению. Default: 24.
- `guest_partners_v1` (str) — текст карточки партнёров (G7).
"""
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GlobalSetting

logger = logging.getLogger(__name__)


async def get_str(session: AsyncSession, key: str, default: str = "") -> str:
    setting = await session.get(GlobalSetting, key)
    if setting and setting.value is not None and setting.value != "":
        return setting.value
    return default


async def get_int(session: AsyncSession, key: str, default: int) -> int:
    """Читает int из GlobalSetting. Если значение пустое или нечисловое —
    возвращает default. Не бросает исключений."""
    setting = await session.get(GlobalSetting, key)
    if not setting or setting.value is None or setting.value == "":
        return default
    try:
        return int(setting.value)
    except (TypeError, ValueError):
        logger.warning(
            f"GlobalSetting[{key}] has non-int value {setting.value!r}, "
            f"falling back to default {default}"
        )
        return default


async def set_value(
    session: AsyncSession,
    key: str,
    value: Optional[str],
    description: Optional[str] = None,
) -> None:
    """Idempotent upsert. Caller отвечает за commit."""
    setting = await session.get(GlobalSetting, key)
    if setting is None:
        setting = GlobalSetting(key=key, value=value, description=description)
        session.add(setting)
    else:
        setting.value = value
        if description is not None:
            setting.description = description


# -------------------------------------------------
# Конкретные ключи с типизированными accessor'ами
# -------------------------------------------------

GUEST_CANCEL_WINDOW_DAYS_KEY = "guest_cancel_window_days"
GUEST_CANCEL_WINDOW_DAYS_DEFAULT = 7

GUEST_INSTRUCTION_OPEN_HOURS_KEY = "guest_instruction_open_hours"
GUEST_INSTRUCTION_OPEN_HOURS_DEFAULT = 24


async def get_guest_cancel_window_days(session: AsyncSession) -> int:
    """Окно отмены брони (в днях до заезда), в течение которого гость
    может отменить сам. Меньше — отправляем к админу."""
    val = await get_int(
        session,
        GUEST_CANCEL_WINDOW_DAYS_KEY,
        GUEST_CANCEL_WINDOW_DAYS_DEFAULT,
    )
    # safety: 0 значит «никогда не даём отменять сам», что валидно
    return max(0, val)


async def get_guest_instruction_open_hours(session: AsyncSession) -> int:
    """За сколько часов до заезда открывается инструкция по заселению."""
    val = await get_int(
        session,
        GUEST_INSTRUCTION_OPEN_HOURS_KEY,
        GUEST_INSTRUCTION_OPEN_HOURS_DEFAULT,
    )
    return max(0, val)


def can_guest_self_cancel(days_to_checkin: int, window_days: int) -> bool:
    """Pure-функция для тестов: гость может сам отменить бронь, только
    если до заезда строго больше `window_days` дней."""
    return days_to_checkin > window_days


def is_instruction_open(hours_to_checkin: float, open_hours: int) -> bool:
    """Pure-функция для тестов: инструкция доступна, если до заезда
    осталось <= `open_hours` часов (включая прошлое)."""
    return hours_to_checkin <= open_hours


# -------------------------------------------------
# G10.6 — двухэтапная оплата (задаток + остаток при заезде)
# -------------------------------------------------

GUEST_ADVANCE_PERCENT_KEY = "guest_advance_percent"
GUEST_ADVANCE_PERCENT_DEFAULT = 30  # 30% от total — типовой задаток


async def get_guest_advance_percent(session: AsyncSession) -> int:
    """% от total_price, который гость вносит как задаток при бронировании.
    Остаток (100% - %) платится при заезде. Default 30."""
    val = await get_int(
        session,
        GUEST_ADVANCE_PERCENT_KEY,
        GUEST_ADVANCE_PERCENT_DEFAULT,
    )
    return max(0, min(100, val))


def compute_advance_amount(total_price: int | float, percent: int) -> int:
    """Pure: рассчитать сумму задатка от total_price по проценту.
    Округление вниз до рубля. percent выходит за [0..100] — clamp'им."""
    if total_price is None:
        return 0
    p = max(0, min(100, int(percent)))
    return int((float(total_price) * p) // 100)


def payment_stage(total: int | float, advance: int | float, required_advance: int) -> str:
    """Pure: определить стадию оплаты.
    - "no_payment" — ничего не оплачено, ждём задаток.
    - "advance_paid" — задаток внесён, ждём остаток.
    - "fully_paid" — оплачено полностью.
    """
    total_i = int(total or 0)
    advance_i = int(advance or 0)
    if advance_i >= total_i and total_i > 0:
        return "fully_paid"
    if advance_i > 0:
        return "advance_paid"
    if advance_i <= 0 and required_advance > 0:
        return "no_payment"
    return "no_payment"
