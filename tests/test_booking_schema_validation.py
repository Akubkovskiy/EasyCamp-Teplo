"""Tests for Pydantic schema validators added during refactoring."""
import pytest
from datetime import date
from decimal import Decimal
import pydantic

from app.schemas.booking import BookingBase
from app.schemas.house import HousePriceBase
from app.models import BookingStatus, BookingSource


def _base_data(**overrides):
    data = dict(
        house_id=1,
        check_in=date(2027, 6, 1),
        check_out=date(2027, 6, 5),
        guest_name="Иван Иванов",
        guest_phone="+7 999 123-45-67",
        guests_count=2,
    )
    data.update(overrides)
    return data


class TestGuestNameValidation:
    def test_valid_name(self):
        b = BookingBase(**_base_data())
        assert b.guest_name == "Иван Иванов"

    def test_strips_whitespace(self):
        b = BookingBase(**_base_data(guest_name="  Петров  "))
        assert b.guest_name == "Петров"

    def test_empty_name_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            BookingBase(**_base_data(guest_name=""))

    def test_whitespace_only_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            BookingBase(**_base_data(guest_name="   "))

    def test_too_long_name_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            BookingBase(**_base_data(guest_name="А" * 151))


class TestGuestPhoneValidation:
    def test_valid_phone_formats(self):
        for phone in ["+7 999 123-45-67", "89991234567", "9991234567", "+79991234567"]:
            b = BookingBase(**_base_data(guest_phone=phone))
            assert b.guest_phone == phone

    def test_none_phone_allowed(self):
        b = BookingBase(**_base_data(guest_phone=None))
        assert b.guest_phone is None

    def test_too_short_phone_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            BookingBase(**_base_data(guest_phone="12345"))


class TestGuestsCountValidation:
    def test_valid_count(self):
        b = BookingBase(**_base_data(guests_count=4))
        assert b.guests_count == 4

    def test_zero_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            BookingBase(**_base_data(guests_count=0))

    def test_negative_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            BookingBase(**_base_data(guests_count=-1))


class TestDateValidation:
    def test_checkout_before_checkin_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            BookingBase(**_base_data(check_in=date(2027, 6, 5), check_out=date(2027, 6, 1)))

    def test_same_day_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            BookingBase(**_base_data(check_in=date(2027, 6, 1), check_out=date(2027, 6, 1)))


class TestHousePriceValidation:
    def test_valid_price(self):
        p = HousePriceBase(
            label="Лето", price_per_night=5000,
            date_from=date(2027, 6, 1), date_to=date(2027, 8, 31)
        )
        assert p.price_per_night == 5000

    def test_zero_price_allowed(self):
        p = HousePriceBase(
            label="Акция", price_per_night=0,
            date_from=date(2027, 6, 1), date_to=date(2027, 6, 30)
        )
        assert p.price_per_night == 0

    def test_negative_price_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            HousePriceBase(
                label="Плохая цена", price_per_night=-100,
                date_from=date(2027, 6, 1), date_to=date(2027, 6, 30)
            )
