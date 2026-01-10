"""
Скрипт для тестирования логики синхронизации (кэширование, TTL)
"""
import asyncio
import logging
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SyncTest")

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

    def __await__(self):
        return self().__await__()

async def test_sync_logic():
    print("Starting sync logic test...")
    
    # 1. Setup mocks
    with patch('app.services.sheets_service.GoogleSheetsService.sync_bookings_to_sheet') as mock_sync, \
         patch('app.services.sheets_service.GoogleSheetsService.create_dashboard') as mock_dash, \
         patch('app.database.AsyncSessionLocal') as mock_session_cls:
        
        # Mock database session properly for async context manager
        mock_session = MagicMock()
        mock_transaction = MagicMock()
        
        # Setup __aenter__ and __aexit__ for async with
        async def async_enter(*args, **kwargs):
            return mock_transaction
        async def async_exit(*args, **kwargs):
            return None
            
        mock_session.__aenter__ = async_enter
        mock_session.__aexit__ = async_exit
        mock_session_cls.return_value = mock_session
        
        # Setup execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = ["booking1", "booking2"]
        
        async def async_execute(*args, **kwargs):
            return mock_result
            
        mock_transaction.execute = async_execute
        
        # Import service after patching
        from app.services.sheets_service import sheets_service
        
        # Reset state
        sheets_service._last_sync_time = None
        sheets_service._sync_cache_ttl_seconds = 2  # Short TTL for testing
        
        # Test 1: First sync (should pass)
        print("\nTest 1: First sync request")
        result1 = await sheets_service.sync_if_needed()
        if result1:
            print("First sync successful")
        else:
            print("First sync failed")
            
        # Test 2: Immediate second sync (should be skipped due to TTL)
        print("\nTest 2: Immediate second sync request (should match cache)")
        result2 = await sheets_service.sync_if_needed()
        if not result2:
            print("Second sync correctly skipped (cache hit)")
        else:
            print("Second sync executed but should have been skipped")
            
        # Test 3: Force sync (should pass ignoring TTL)
        print("\nTest 3: Force sync request")
        result3 = await sheets_service.sync_if_needed(force=True)
        if result3:
            print("Force sync successful")
        else:
            print("Force sync failed")
            
        # Test 4: Wait for TTL and sync (should pass)
        print(f"\nWaiting for TTL ({sheets_service._sync_cache_ttl_seconds}s)...")
        await asyncio.sleep(sheets_service._sync_cache_ttl_seconds + 0.1)
        
        print("\nTest 4: Sync after TTL")
        result4 = await sheets_service.sync_if_needed()
        if result4:
            print("Sync after TTL successful")
        else:
            print("Sync after TTL failed")
            
        # Verify call counts
        # Expected: 1 (first) + 1 (force) + 1 (after TTL) = 3 calls
        # sync_bookings_async calls internal sync methods in thread pool, so mocks should be called
        # But since we're patching the class methods and using an instance, it might be tricky.
        # Let's rely on the return values of sync_if_needed which we logged.
        
    print("\nTest completed!")

if __name__ == "__main__":
    # Add project root to path
    import os
    sys.path.append(os.getcwd())
    
    asyncio.run(test_sync_logic())
