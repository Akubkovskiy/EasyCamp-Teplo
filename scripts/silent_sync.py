import asyncio
import sys
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        from app.services.sheets_service import sheets_service
        logger.info("Starting sync...")
        # force=True to bypass TTL cache
        success = await sheets_service.sync_if_needed(force=True)
        if success:
            logger.info("Sync completed successfully.")
        else:
            logger.info("Sync skipped or failed.")
    except Exception as e:
        logger.error(f"Sync error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
