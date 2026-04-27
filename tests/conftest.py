"""
Pytest configuration for EasyCamp tests
"""
import os
import pytest
import asyncio
import sys
from pathlib import Path

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test-friendly defaults — без них `app.core.config` падает при импорте,
# когда .env отсутствует (CI, sandbox, локальный pytest без env).
# Token must pass aiogram's basic format check `\d+:[A-Za-z0-9_-]{35,}`
os.environ.setdefault(
    "TELEGRAM_BOT_TOKEN",
    "1234567890:AAEhBP0av28cxuwxxxxxxxxxxxxxxxxxxxx",
)
os.environ.setdefault("TELEGRAM_CHAT_ID", "1")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_booking_data():
    """Sample data for booking creation"""
    from datetime import date
    return {
        'house_id': 1,
        'guest_name': 'Test Guest',
        'guest_phone': '+79001234567',
        'check_in': date(2026, 3, 1),
        'check_out': date(2026, 3, 5),
        'guests_count': 2,
        'total_price': 10000,
    }


@pytest.fixture
def sample_webhook_payload():
    """Sample Avito webhook payload"""
    return {
        "event_type": "booking",
        "payload": {
            "avito_booking_id": "12345678",
            "date_start": "2026-03-01",
            "date_end": "2026-03-05",
            "guest_name": "Тестовый Гость",
            "guest_phone": "+79001234567",
            "nights": 4,
            "safeCrate": {"amount": 10000},
            "status": "confirmed"
        }
    }
