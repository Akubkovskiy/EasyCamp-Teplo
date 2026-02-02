"""
Периодическая задача синхронизации с Google Sheets
"""

import asyncio
import logging


logger = logging.getLogger(__name__)


async def sync_sheets_job():
    """Периодическая синхронизация с Google Sheets с retry логикой"""
    logger.info("📊 Starting scheduled Google Sheets sync...")

    max_retries = 3
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            # Use the smart sync method which handles caching
            from app.services.sheets_service import sheets_service

            success = await sheets_service.sync_if_needed(force=False)

            if success:
                logger.info("✅ Scheduled sync completed successfully")
            else:
                logger.debug("Scheduled sync skipped (cache hit or no data)")

            return  # Success, exit

        except Exception as e:
            attempt_num = attempt + 1
            if attempt_num < max_retries:
                wait_time = retry_delay * attempt_num  # Exponential backoff
                logger.warning(
                    f"❌ Sync attempt {attempt_num}/{max_retries} failed: {e}"
                )
                logger.info(f"⏳ Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"❌ Sheets sync failed after {max_retries} attempts: {e}",
                    exc_info=True,
                )
