"""
Периодические задачи ценообразования:
1. Авто-скидки на свободные даты (горящие предложения)
2. Синхронизация цен с Авито

Управляется настройками:
- ENABLE_AUTO_DISCOUNTS (true/false)
- ENABLE_AVITO_PRICE_SYNC (true/false)
"""

import logging
from app.core.config import settings
from app.database import AsyncSessionLocal
from app.services.pricing_service import PricingService
from app.services.avito_price_service import sync_prices_to_avito

logger = logging.getLogger(__name__)


async def auto_discount_job():
    """
    Проверяет загруженность на ближайшие дни.
    Если домик свободен завтра/послезавтра — создаёт горящую скидку.
    Запускается 2 раза в день (утром и вечером).
    """
    if not settings.enable_auto_discounts:
        logger.info("Auto-discounts disabled (ENABLE_AUTO_DISCOUNTS=false), skipping")
        return []

    logger.info("Running auto-discount job...")

    try:
        async with AsyncSessionLocal() as db:
            applied = await PricingService.check_and_apply_auto_discounts(db)

        if applied:
            for d in applied:
                logger.info(
                    f"Auto-discount applied: {d['house']} on {d['date']} → -{d['percent']}%"
                )
            logger.info(f"Auto-discount job: {len(applied)} discounts created")
        else:
            logger.info("Auto-discount job: no discounts needed")

        return applied

    except Exception as e:
        logger.error(f"Auto-discount job failed: {e}", exc_info=True)
        return []


async def avito_price_sync_job():
    """
    Синхронизирует текущие цены (base + сезонные + скидки) на Авито.
    Запускается после авто-скидок и по расписанию.
    """
    if not settings.enable_avito_price_sync:
        logger.info("Avito price sync disabled (ENABLE_AVITO_PRICE_SYNC=false), skipping")
        return {"synced": [], "errors": []}

    logger.info("Running Avito price sync job...")

    try:
        async with AsyncSessionLocal() as db:
            result = await sync_prices_to_avito(db)

        synced = result.get("synced", [])
        errors = result.get("errors", [])

        for s in synced:
            logger.info(f"Price sync OK: {s['house']} → Avito item {s['item_id']} ({s['days']} days)")
        for e in errors:
            logger.error(f"Price sync error: {e}")

        logger.info(f"Avito price sync: {len(synced)} synced, {len(errors)} errors")
        return result

    except Exception as e:
        logger.error(f"Avito price sync job failed: {e}", exc_info=True)
        return {"synced": [], "errors": [str(e)]}


async def pricing_cycle_job():
    """
    Полный цикл: сначала проверяем скидки, потом синхронизируем цены на Авито.
    """
    logger.info("=== Pricing cycle started ===")
    await auto_discount_job()
    await avito_price_sync_job()
    logger.info("=== Pricing cycle completed ===")
