"""Shared display constants for booking status and source."""

from app.models import BookingSource, BookingStatus

BOOKING_STATUS_EMOJI: dict[BookingStatus, str] = {
    BookingStatus.NEW: "🆕",
    BookingStatus.CONFIRMED: "✅",
    BookingStatus.PAID: "💰",
    BookingStatus.CHECKING_IN: "🔔",
    BookingStatus.CHECKED_IN: "🏠",
    BookingStatus.CANCELLED: "❌",
    BookingStatus.COMPLETED: "🏁",
}

BOOKING_STATUS_NAMES: dict[BookingStatus, str] = {
    BookingStatus.NEW: "Ожидает",
    BookingStatus.CONFIRMED: "Подтверждено",
    BookingStatus.PAID: "Оплачено",
    BookingStatus.CHECKING_IN: "Заезд сегодня",
    BookingStatus.CHECKED_IN: "Проживает",
    BookingStatus.CANCELLED: "Отменено",
    BookingStatus.COMPLETED: "Завершено",
}

BOOKING_SOURCE_EMOJI: dict[BookingSource, str] = {
    BookingSource.AVITO: "🅰️",
    BookingSource.TELEGRAM: "💬",
    BookingSource.DIRECT: "🌐",
}
