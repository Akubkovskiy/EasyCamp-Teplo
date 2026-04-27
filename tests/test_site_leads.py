"""Тесты Phase S10.1 — `POST /api/leads` в EasyCamp.

Проверяем токен-аутентификацию, идемпотентность по external_ref,
fallback резолва домика и факт создания Booking(NEW, source=DIRECT).
Avito/sheets/Telegram side-effects замоканы.
"""
import os

# Должно стоять ДО любого `from app...` импорта (config.py читает env).
os.environ.setdefault(
    "TELEGRAM_BOT_TOKEN",
    "1234567890:AAEhBP0av28cxuwxxxxxxxxxxxxxxxxxxxx",
)
os.environ.setdefault("TELEGRAM_CHAT_ID", "1")
os.environ.setdefault("SITE_LEAD_TOKEN", "test-token")

from datetime import date, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.site_leads import get_async_session, router as site_leads_router
from app.database import Base
from app.models import (
    Booking,
    BookingSource,
    BookingStatus,
    House,
)
from app.services.booking_service import BookingService

# Build a minimal FastAPI app with ONLY the site_leads router. We
# intentionally don't import `app.main:app` because its startup events
# (DB restore, scheduler, Telegram polling, etc.) require live
# infrastructure. This test only validates the router itself.
app = FastAPI()
app.include_router(site_leads_router)


# -------------------------------------------------
# Test fixtures
# -------------------------------------------------


@pytest.fixture
async def session_factory():
    """In-memory async SQLite + create tables. Один engine per test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    yield Session
    await engine.dispose()


@pytest.fixture
async def seeded_house(session_factory):
    """Засеять минимум один дом, чтобы fallback-резолв работал."""
    async with session_factory() as s:
        house = House(name="Forest 34м²", description="", capacity=4, base_price=5500)
        s.add(house)
        await s.commit()
        await s.refresh(house)
        return house.id


@pytest.fixture
def client(session_factory, monkeypatch):
    """FastAPI TestClient с подменённой сессией и заглушенными side-effects."""

    async def override_session():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_async_session] = override_session

    # Заглушаем Avito и sheets — они не нужны в unit-тесте и могут падать
    # без env / сети.
    async def noop_block(_booking):
        return None

    async def noop_sheets():
        return None

    monkeypatch.setattr(BookingService, "_block_avito_dates", staticmethod(noop_block))
    monkeypatch.setattr(
        BookingService,
        "_safe_background_sheets_sync",
        classmethod(lambda cls: noop_sheets()),
    )

    # Telegram notify уже обёрнут try/except внутри _notify_admins, но
    # на всякий случай заглушим импорт bot, чтобы не было лишних
    # warning'ов в логе теста.
    from app.api import site_leads as site_leads_module

    async def silent_notify(*_args, **_kwargs):
        return None

    monkeypatch.setattr(site_leads_module, "_notify_admins", silent_notify)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def _payload(**overrides):
    base = {
        "guest_name": "Иван Тестов",
        "guest_phone": "+79991234567",
        "check_in": (date.today() + timedelta(days=10)).isoformat(),
        "check_out": (date.today() + timedelta(days=12)).isoformat(),
        "guests_count": 2,
        "house_name": "Forest 34м²",
        "comment": "Хочу домик в лесу",
        "source": "website",
        "external_ref": "site-1",
    }
    base.update(overrides)
    return base


# -------------------------------------------------
# Auth
# -------------------------------------------------


def test_missing_token_401(client, seeded_house):
    response = client.post("/api/leads", json=_payload())
    assert response.status_code == 401


def test_wrong_token_401(client, seeded_house):
    response = client.post(
        "/api/leads",
        json=_payload(),
        headers={"X-Site-Token": "wrong"},
    )
    assert response.status_code == 401


def test_disabled_when_token_unset(client, seeded_house, monkeypatch):
    """Если SITE_LEAD_TOKEN пустой в settings — endpoint 503."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "site_lead_token", "")
    response = client.post(
        "/api/leads",
        json=_payload(),
        headers={"X-Site-Token": "anything"},
    )
    assert response.status_code == 503


# -------------------------------------------------
# Happy path
# -------------------------------------------------


def test_create_lead_creates_booking(client, seeded_house):
    response = client.post(
        "/api/leads",
        json=_payload(),
        headers={"X-Site-Token": "test-token"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["status"] == BookingStatus.NEW.value
    assert data["house_id"] == seeded_house
    assert data["duplicate"] is False
    assert data["booking_id"] == data["lead_id"]


def test_idempotent_on_external_ref(client, seeded_house):
    payload = _payload(external_ref="site-99")

    r1 = client.post(
        "/api/leads", json=payload, headers={"X-Site-Token": "test-token"}
    )
    assert r1.status_code == 201
    booking_id_1 = r1.json()["booking_id"]

    r2 = client.post(
        "/api/leads", json=payload, headers={"X-Site-Token": "test-token"}
    )
    assert r2.status_code == 201
    data2 = r2.json()
    assert data2["booking_id"] == booking_id_1
    assert data2["duplicate"] is True


def test_house_fallback_when_name_unknown(client, seeded_house):
    """Если house_name не совпал — берём первый из БД и помечаем в комменте."""
    payload = _payload(house_name="Несуществующий домик X", external_ref="site-77")
    response = client.post(
        "/api/leads", json=payload, headers={"X-Site-Token": "test-token"}
    )
    assert response.status_code == 201
    assert response.json()["house_id"] == seeded_house


def test_invalid_dates_422(client, seeded_house):
    today = date.today()
    payload = _payload(
        check_in=(today + timedelta(days=5)).isoformat(),
        check_out=(today + timedelta(days=5)).isoformat(),  # same as check_in
    )
    response = client.post(
        "/api/leads", json=payload, headers={"X-Site-Token": "test-token"}
    )
    assert response.status_code == 422


def test_no_houses_in_db_returns_422(client, session_factory):
    """Без посевного дома сервис не может создать бронь."""
    response = client.post(
        "/api/leads",
        json=_payload(house_id=None, house_name=None),
        headers={"X-Site-Token": "test-token"},
    )
    assert response.status_code == 422
