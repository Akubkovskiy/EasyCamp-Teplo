"""Shared utilities for the checkout acknowledgment flow."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models import GlobalSetting


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
    s = await session.get(GlobalSetting, ack_key(booking_id))
    return s.value if s else None


async def set_ack_status(session, booking_id: int, value: str) -> None:
    key = ack_key(booking_id)
    s = await session.get(GlobalSetting, key)
    if s:
        s.value = value
    else:
        session.add(GlobalSetting(key=key, value=value))
    await session.commit()
