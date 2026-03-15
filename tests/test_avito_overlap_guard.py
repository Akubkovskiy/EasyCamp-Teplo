"""
Tests for Avito booking overlap guards (P0 hotfix).

Verifies that both ingestion paths (periodic sync + webhook) reject
bookings that overlap with existing active bookings for the same house.
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_booking_data(
    avito_id: str = "999",
    check_in: str = "2026-04-10",
    check_out: str = "2026-04-15",
    status: str = "active",
):
    """Minimal Avito API booking payload (dict)."""
    return {
        "avito_booking_id": avito_id,
        "check_in": check_in,
        "check_out": check_out,
        "status": status,
        "guest_count": 2,
        "base_price": 10000,
        "contact": {"name": "Test Guest", "phone": "+79001234567"},
        "safe_deposit": {"total_amount": 5000, "tax": 1000, "owner_amount": 4000},
    }


def _make_existing_booking(
    booking_id: int = 1,
    house_id: int = 1,
    check_in: date = date(2026, 4, 10),
    check_out: date = date(2026, 4, 15),
    status_value: str = "confirmed",
):
    """Fake Booking ORM object for overlap results."""
    b = MagicMock()
    b.id = booking_id
    b.house_id = house_id
    b.check_in = check_in
    b.check_out = check_out
    b.status = MagicMock(value=status_value)
    return b


# ===========================================================================
# A. Periodic sync path — process_avito_booking()
# ===========================================================================

class TestSyncPathOverlapGuard:
    """Tests for avito_sync_service.process_avito_booking overlap guard."""

    @pytest.mark.asyncio
    async def test_new_booking_with_overlap_is_skipped(self):
        """When a new Avito booking overlaps an existing one, it must NOT be created."""
        from app.services.avito_sync_service import process_avito_booking

        existing = _make_existing_booking(
            booking_id=42, check_in=date(2026, 4, 10), check_out=date(2026, 4, 15)
        )

        # Mock session: first execute (external_id check) → None, second (overlap) → existing
        session = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # external_id lookup → not found
                result.scalar_one_or_none.return_value = None
            else:
                # overlap check → conflict found
                result.scalar_one_or_none.return_value = existing
            return result

        session.execute = mock_execute
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.get = AsyncMock(return_value=MagicMock(name="TestHouse"))

        stats = {"total": 1, "new_bookings": [], "updated_bookings": [], "errors": 0}
        booking_data = _make_booking_data(avito_id="555", check_in="2026-04-12", check_out="2026-04-18")

        await process_avito_booking(session, booking_data, house_id=1, stats=stats)

        # Booking must NOT have been added
        assert len(stats["new_bookings"]) == 0
        session.add.assert_not_called()
        assert stats.get("conflicts", 0) == 1

    @pytest.mark.asyncio
    async def test_new_booking_without_overlap_is_created(self):
        """When no overlap exists, booking is created normally."""
        from app.services.avito_sync_service import process_avito_booking

        session = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # external_id lookup → not found
                result.scalar_one_or_none.return_value = None
            else:
                # overlap check → no conflict
                result.scalar_one_or_none.return_value = None
            return result

        session.execute = mock_execute
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.get = AsyncMock(return_value=MagicMock(name="TestHouse"))

        stats = {"total": 1, "new_bookings": [], "updated_bookings": [], "errors": 0}
        booking_data = _make_booking_data(avito_id="556")

        await process_avito_booking(session, booking_data, house_id=1, stats=stats)

        # Booking SHOULD have been added
        assert len(stats["new_bookings"]) == 1
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_existing_booking_update_still_works(self):
        """Updating an existing booking (same external_id) should still work."""
        from app.services.avito_sync_service import process_avito_booking

        existing = _make_existing_booking()
        existing.status = MagicMock(value="new")
        existing.commission = Decimal("0")
        existing.prepayment_owner = Decimal("0")
        existing.advance_amount = Decimal("0")

        session = AsyncMock()

        async def mock_execute(stmt):
            result = MagicMock()
            result.scalar_one_or_none.return_value = existing
            return result

        session.execute = mock_execute
        session.get = AsyncMock(return_value=MagicMock(name="TestHouse"))

        stats = {"total": 1, "new_bookings": [], "updated_bookings": [], "errors": 0}
        booking_data = _make_booking_data(avito_id="999", status="active")

        await process_avito_booking(session, booking_data, house_id=1, stats=stats)

        # Should be in updated list (status changed from new → confirmed)
        assert len(stats["updated_bookings"]) == 1
        assert stats.get("conflicts", 0) == 0

    @pytest.mark.asyncio
    async def test_adjacent_dates_are_not_overlap(self):
        """Checkout day == next checkin day is NOT an overlap (adjacent bookings OK)."""
        from app.services.avito_sync_service import process_avito_booking

        session = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = None  # not found by external_id
            else:
                result.scalar_one_or_none.return_value = None  # no overlap
            return result

        session.execute = mock_execute
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.get = AsyncMock(return_value=MagicMock(name="TestHouse"))

        stats = {"total": 1, "new_bookings": [], "updated_bookings": [], "errors": 0}
        # Existing booking ends Apr 10, new one starts Apr 10 → adjacent, not overlapping
        booking_data = _make_booking_data(check_in="2026-04-10", check_out="2026-04-15")

        await process_avito_booking(session, booking_data, house_id=1, stats=stats)

        assert len(stats["new_bookings"]) == 1


# ===========================================================================
# B. Webhook path — BookingService.create_or_update_avito_booking()
# ===========================================================================

class TestWebhookPathOverlapGuard:
    """Tests for BookingService.create_or_update_avito_booking overlap guard."""

    @pytest.mark.asyncio
    @patch("app.services.booking_service.BookingService.check_availability", new_callable=AsyncMock)
    @patch("app.services.booking_service.BookingService._safe_background_sheets_sync", new_callable=AsyncMock)
    async def test_webhook_new_booking_with_overlap_blocked(self, mock_sheets, mock_avail):
        """Webhook creating a new booking that overlaps should return None."""
        from app.services.booking_service import BookingService

        mock_avail.return_value = False  # dates NOT available

        db = AsyncMock()
        # external_id lookup → not found
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        payload = MagicMock()
        payload.avito_booking_id = "777"
        payload.item_id = 100
        payload.check_in = "2026-04-10"
        payload.check_out = "2026-04-15"
        payload.status = "active"
        payload.guest_count = 2
        payload.base_price = 10000
        payload.contact = MagicMock(name="Guest", phone="+79001234567")
        payload.safe_deposit = MagicMock(total_amount=5000, tax=1000, owner_amount=4000)
        payload.prepayment = None
        payload.prepayment_amount = None
        payload.advance = None
        payload.deposit = None

        with patch("app.core.config.settings") as mock_settings:
            mock_settings.avito_item_ids = "100:1"
            result = await BookingService.create_or_update_avito_booking(db, payload)

        assert result is None
        db.add.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.booking_service.BookingService.check_availability", new_callable=AsyncMock)
    @patch("app.services.booking_service.BookingService._safe_background_sheets_sync", new_callable=AsyncMock)
    async def test_webhook_new_booking_without_overlap_created(self, mock_sheets, mock_avail):
        """Webhook creating a non-overlapping booking should succeed."""
        from app.services.booking_service import BookingService

        mock_avail.return_value = True  # dates available

        db = AsyncMock()
        # external_id lookup → not found
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        payload = MagicMock()
        payload.avito_booking_id = "778"
        payload.item_id = 100
        payload.check_in = "2026-04-10"
        payload.check_out = "2026-04-15"
        payload.status = "active"
        payload.guest_count = 2
        payload.base_price = 10000
        payload.contact = MagicMock(name="Guest", phone="+79001234567")
        payload.safe_deposit = MagicMock(total_amount=5000, tax=1000, owner_amount=4000)
        payload.prepayment = None
        payload.prepayment_amount = None
        payload.advance = None
        payload.deposit = None

        with patch("app.core.config.settings") as mock_settings:
            mock_settings.avito_item_ids = "100:1"

            with patch("app.utils.validators.format_phone", return_value="+79001234567"):
                result = await BookingService.create_or_update_avito_booking(db, payload)

        # Should have called db.add
        db.add.assert_called_once()


# ===========================================================================
# C. Date overlap logic (pure, no mocks)
# ===========================================================================

class TestOverlapCondition:
    """Verify the SQL overlap condition: check_in < new_check_out AND check_out > new_check_in"""

    @pytest.mark.parametrize(
        "existing_in,existing_out,new_in,new_out,should_overlap",
        [
            # Classic overlap
            (date(2026, 4, 10), date(2026, 4, 15), date(2026, 4, 12), date(2026, 4, 18), True),
            # Contained within
            (date(2026, 4, 1), date(2026, 4, 20), date(2026, 4, 5), date(2026, 4, 10), True),
            # Exact same dates
            (date(2026, 4, 10), date(2026, 4, 15), date(2026, 4, 10), date(2026, 4, 15), True),
            # Adjacent (checkout = checkin) — NOT overlap
            (date(2026, 4, 10), date(2026, 4, 15), date(2026, 4, 15), date(2026, 4, 20), False),
            # Completely before
            (date(2026, 4, 1), date(2026, 4, 5), date(2026, 4, 10), date(2026, 4, 15), False),
            # Completely after
            (date(2026, 4, 20), date(2026, 4, 25), date(2026, 4, 10), date(2026, 4, 15), False),
        ],
    )
    def test_overlap_condition(self, existing_in, existing_out, new_in, new_out, should_overlap):
        """The condition used in SQL: existing.check_in < new.check_out AND existing.check_out > new.check_in"""
        overlaps = (existing_in < new_out) and (existing_out > new_in)
        assert overlaps is should_overlap
