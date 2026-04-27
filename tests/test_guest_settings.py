"""Unit-тесты для pure-функций конфигурируемых правил гостя
(Phase G10.3). DB не нужна, aiogram не нужен."""
from app.services.global_settings import (
    can_guest_self_cancel,
    is_instruction_open,
)


# -------------------------------------------------
# can_guest_self_cancel(days_to_checkin, window_days)
# -------------------------------------------------


def test_cancel_inside_window_blocked():
    # Окно 7, до заезда 5 — нельзя самому
    assert can_guest_self_cancel(5, 7) is False
    # граница: 7 == 7 — нельзя (строго больше)
    assert can_guest_self_cancel(7, 7) is False


def test_cancel_outside_window_allowed():
    # До заезда 8 — можно самому при окне 7
    assert can_guest_self_cancel(8, 7) is True
    assert can_guest_self_cancel(30, 7) is True


def test_cancel_zero_days_blocked():
    assert can_guest_self_cancel(0, 7) is False
    assert can_guest_self_cancel(-1, 7) is False  # уже заехал


def test_cancel_window_zero_means_never_self_cancel_for_today():
    # Окно 0 значит «нельзя если сегодня и раньше»; завтра уже можно
    assert can_guest_self_cancel(0, 0) is False
    assert can_guest_self_cancel(1, 0) is True


# -------------------------------------------------
# is_instruction_open(hours_to_checkin, open_hours)
# -------------------------------------------------


def test_instruction_closed_far_in_future():
    # До заезда 48 ч, окно 24 ч — закрыто
    assert is_instruction_open(48.0, 24) is False


def test_instruction_open_at_window_boundary():
    # До заезда ровно 24 ч, окно 24 ч — открыто (<=)
    assert is_instruction_open(24.0, 24) is True


def test_instruction_open_close_to_checkin():
    assert is_instruction_open(2.0, 24) is True


def test_instruction_open_when_already_started():
    # Уже заехал (отрицательные часы) — инструкция всё равно открыта
    assert is_instruction_open(-3.0, 24) is True


def test_custom_window_48_hours():
    assert is_instruction_open(40.0, 48) is True
    assert is_instruction_open(50.0, 48) is False
