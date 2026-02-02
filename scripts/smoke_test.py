import asyncio
import logging
import sys
import os

sys.path.append(os.getcwd())

from app.main import app
from app.core.config import settings
from app.database import AsyncSessionLocal
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def smoke_test():
    logger.info("💨 Starting Smoke Test...")
    
    # 1. Config Check
    logger.info(f"✅ Config loaded. Project DB: {settings.database_url}")
    assert settings.telegram_bot_token, "Token missing"
    
    # 2. Database Connection Check
    logger.info("🔌 Testing Database Connection...")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    # 3. App Startup Simulation
    logger.info("🚀 Testing App Startup Events...")
    try:
        # Simulate lifespan
        async with app.router.lifespan_context(app):
            logger.info("✅ Startup events completed without error")
            
            # 4. Check Rate Limiter
            if hasattr(app.state, "limiter"):
                logger.info(f"✅ Rate Limiter initialized: Enabled={app.state.limiter.enabled}")
            else:
                logger.error("❌ Rate Limiter NOT found in app state")
                raise Exception("Rate Limiter missing")

    except Exception as e:
        logger.error(f"❌ App startup failed: {e}")
        raise

    logger.info("🎉 Smoke Test Passed! System is ready.")

if __name__ == "__main__":
    asyncio.run(smoke_test())
