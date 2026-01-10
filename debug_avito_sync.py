import asyncio
import logging
import sys
from app.core.config import settings
from app.jobs.avito_sync_job import sync_avito_job

# Configure logging to show info
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

async def main():
    print("--- Starting Manual Avito Sync in Debug Mode ---")
    await sync_avito_job()
    print("--- Sync Completed ---")

if __name__ == "__main__":
    asyncio.run(main())
