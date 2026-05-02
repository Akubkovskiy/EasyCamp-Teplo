"""
Абстракция синхронизации цен с внешними площадками.

Сейчас поддерживается только Авито. В будущем добавляем:
- Booking.com  → зарегистрировать в PLATFORMS
- Airbnb       → зарегистрировать в PLATFORMS
- Ostrovok     → зарегистрировать в PLATFORMS

Как добавить новую площадку:
    1. Создать async def sync_<platform>(db, house_id, days_forward) -> SyncResult
    2. Добавить в PLATFORMS словарь ниже
    3. Задать env-флаг ENABLE_<PLATFORM>_PRICE_SYNC в config.py
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

# GlobalSetting ключ для хранения timestamp последнего синка
_LAST_SYNC_KEY = "price_sync_last_at"


@dataclass
class SyncResult:
    platform: str
    synced: list = field(default_factory=list)   # [{house, item_id, days}]
    errors: list = field(default_factory=list)    # [str]
    skipped: bool = False                          # площадка не сконфигурирована

    @property
    def ok(self) -> bool:
        return bool(self.synced) and not self.errors


async def _sync_avito(db: AsyncSession, house_id: Optional[int], days_forward: int) -> SyncResult:
    """Делегирует в avito_price_service."""
    if not settings.enable_avito_price_sync:
        return SyncResult(platform="avito", skipped=True)

    from app.services.avito_price_service import sync_prices_to_avito
    raw = await sync_prices_to_avito(db, house_id=house_id, days_forward=days_forward)
    return SyncResult(
        platform="avito",
        synced=raw.get("synced", []),
        errors=raw.get("errors", []),
    )


async def _sync_yandex_travel(db: AsyncSession, house_id: Optional[int], days_forward: int) -> SyncResult:
    """Синхронизация цен на Яндекс Путешествия."""
    if not settings.enable_yandex_travel_price_sync:
        return SyncResult(platform="yandex_travel", skipped=True)
    if not settings.yandex_travel_oauth_token or not settings.yandex_travel_room_ids:
        return SyncResult(platform="yandex_travel", skipped=True)

    from app.services.yandex_travel_api_service import yandex_travel_api_service
    from app.services.pricing_service import PricingService
    from app.models import House
    from sqlalchemy import select
    from datetime import date, timedelta

    mapping_str = settings.yandex_travel_room_ids
    hotel_room_mapping = {}
    for pair in mapping_str.split(","):
        pair = pair.strip()
        if ":" not in pair:
            continue
        key, hid_str = pair.rsplit(":", 1)
        try:
            hotel_id, _, room_id = key.strip().partition("/")
            hotel_room_mapping[int(hid_str.strip())] = (hotel_id.strip(), room_id.strip())
        except ValueError:
            pass

    synced = []
    errors = []
    today = date.today()

    stmt = select(House)
    if house_id:
        stmt = stmt.where(House.id == house_id)
    result = await db.execute(stmt)
    houses = result.scalars().all()

    for house in houses:
        if house.id not in hotel_room_mapping:
            continue
        hotel_id, room_id = hotel_room_mapping[house.id]
        price_entries = []
        for i in range(days_forward):
            target_date = today + timedelta(days=i)
            info = await PricingService.get_price_for_date(db, house.id, target_date)
            price_entries.append({
                "date": target_date.isoformat(),
                "price": info["final_price"],
            })
        ok = yandex_travel_api_service.update_prices(hotel_id, room_id, price_entries)
        if ok:
            synced.append({"house": house.name, "hotel_id": hotel_id, "room_id": room_id, "days": days_forward})
        else:
            errors.append(f"{house.name}: price update failed")

    return SyncResult(platform="yandex_travel", synced=synced, errors=errors)


# Реестр платформ. Ключ — имя, значение — coroutine factory.
# Чтобы отключить площадку: уберите её из словаря или поставьте флаг в конфиге.
_PLATFORMS = {
    "avito": _sync_avito,
    "yandex_travel": _sync_yandex_travel,
    # "booking": _sync_booking,  # добавить когда появится
}


async def sync_all_platforms(
    db: AsyncSession,
    house_id: Optional[int] = None,
    days_forward: int = 90,
) -> list[SyncResult]:
    """
    Синхронизирует цены на все зарегистрированные площадки.
    Возвращает список SyncResult — по одному на платформу.
    """
    results: list[SyncResult] = []
    for name, fn in _PLATFORMS.items():
        try:
            result = await fn(db, house_id, days_forward)
            results.append(result)
            if result.skipped:
                logger.debug("Platform %s: skipped (not configured)", name)
            elif result.ok:
                logger.info("Platform %s: synced %d house(s)", name, len(result.synced))
            else:
                logger.warning("Platform %s: errors: %s", name, result.errors)
        except Exception as e:
            logger.error("Platform %s: unhandled error: %s", name, e, exc_info=True)
            results.append(SyncResult(platform=name, errors=[str(e)]))

    await _record_sync_timestamp(db)
    return results


async def _record_sync_timestamp(db: AsyncSession) -> None:
    """Сохраняет время последнего синка в GlobalSetting."""
    try:
        from app.services import global_settings
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        await global_settings.set_value(db, _LAST_SYNC_KEY, now_str)
        await db.commit()
    except Exception as e:
        logger.warning("Could not record sync timestamp: %s", e)


async def get_last_sync_time(db: AsyncSession) -> Optional[str]:
    """Возвращает строку с временем последнего синка или None."""
    try:
        from app.services import global_settings
        return await global_settings.get_str(db, _LAST_SYNC_KEY, default=None)
    except Exception:
        return None


def format_sync_results(results: list[SyncResult]) -> str:
    """Форматирует список SyncResult в человекочитаемую строку для Telegram."""
    lines = []
    for r in results:
        if r.skipped:
            lines.append(f"⏭ {r.platform.capitalize()}: не настроено")
        elif r.ok:
            total_days = sum(s.get("days", 0) for s in r.synced)
            houses = ", ".join(s["house"] for s in r.synced)
            lines.append(f"✅ {r.platform.capitalize()}: {houses} ({total_days} дн.)")
        else:
            lines.append(f"❌ {r.platform.capitalize()}: {'; '.join(r.errors)}")
    return "\n".join(lines) if lines else "Нет настроенных площадок"
