"""
Сервис синхронизации цен с Avito.
Берёт цены из базы (base_price + сезонные + скидки) и отправляет на Авито.
"""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.avito_api_service import avito_api_service
from app.services.pricing_service import PricingService
from app.services.house_service import HouseService

logger = logging.getLogger(__name__)


def parse_avito_item_ids() -> Dict[int, int]:
    """
    Парсит AVITO_ITEM_IDS из настроек.
    Формат: "avito_item_id:house_id,avito_item_id:house_id"
    Возвращает: {house_id: avito_item_id}
    """
    mapping: Dict[int, int] = {}
    raw = settings.avito_item_ids
    if not raw:
        return mapping

    for pair in raw.split(","):
        pair = pair.strip()
        if ":" not in pair:
            continue
        parts = pair.split(":")
        try:
            avito_item_id = int(parts[0])
            house_id = int(parts[1])
            mapping[house_id] = avito_item_id
        except (ValueError, IndexError):
            logger.warning(f"Invalid AVITO_ITEM_IDS pair: {pair}")
    return mapping


async def sync_prices_to_avito(
    db: AsyncSession,
    house_id: Optional[int] = None,
    days_forward: int = 90,
) -> Dict:
    """
    Синхронизирует цены из базы на Авито.

    Args:
        db: Сессия БД
        house_id: Конкретный домик (None = все)
        days_forward: На сколько дней вперёд

    Returns:
        {"synced": [...], "errors": [...]}
    """
    item_mapping = parse_avito_item_ids()
    if not item_mapping:
        logger.warning("AVITO_ITEM_IDS not configured, skipping price sync")
        return {"synced": [], "errors": ["AVITO_ITEM_IDS not configured"]}

    houses = await HouseService.get_all_houses(db)
    if house_id:
        houses = [h for h in houses if h.id == house_id]

    today = date.today()
    results = {"synced": [], "errors": []}

    for house in houses:
        avito_item_id = item_mapping.get(house.id)
        if not avito_item_id:
            logger.info(f"House {house.name} (id={house.id}) has no Avito item mapping")
            continue

        # Собираем цены по дням
        price_entries = []
        for i in range(days_forward):
            target_date = today + timedelta(days=i)
            info = await PricingService.get_price_for_date(db, house.id, target_date)
            price_entries.append({
                "date": target_date.isoformat(),
                "price": info["final_price"],
            })

        try:
            success = avito_api_service.update_prices(avito_item_id, price_entries)
            if success:
                results["synced"].append({
                    "house": house.name,
                    "item_id": avito_item_id,
                    "days": len(price_entries),
                })
                logger.info(
                    f"Synced {len(price_entries)} price days for {house.name} → Avito item {avito_item_id}"
                )
            else:
                results["errors"].append(f"{house.name}: Avito API returned error")
        except Exception as e:
            logger.error(f"Failed to sync prices for {house.name}: {e}")
            results["errors"].append(f"{house.name}: {str(e)}")

    return results
