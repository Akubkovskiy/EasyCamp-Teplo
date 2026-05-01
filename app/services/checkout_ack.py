"""Shared utilities for the checkout acknowledgment flow."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services import global_settings


def ack_key(booking_id: int) -> str:
    return f"ack_checkout_{booking_id}"


def checkout_ack_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Принял(а), жду!",
            callback_data=f"cleaner:ack_checkout:{booking_id}",
        ),
        InlineKeyboardButton(
            text="😷 Не смогу",
            callback_data=f"cleaner:decline_checkout:{booking_id}",
        ),
    ]])


async def get_ack_status(session, booking_id: int) -> str | None:
    """Return current ack state or None if not set."""
    val = await global_settings.get_str(session, ack_key(booking_id), default="")
    return val if val else None


async def set_ack_status(session, booking_id: int, value: str) -> None:
    """Upsert ack state and commit."""
    await global_settings.set_value(session, ack_key(booking_id), value)
    await session.commit()
