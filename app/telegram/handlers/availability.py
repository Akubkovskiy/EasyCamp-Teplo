import datetime
import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from app.telegram.ui.calendar import build_month_keyboard, month_title
from app.telegram.state.availability import (
    availability_states,
    AvailabilityState,
)

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(lambda c: c.data == "admin:availability")
async def start_availability(callback: CallbackQuery):
    if callback.from_user is None or callback.message is None:
        return

    user_id = callback.from_user.id
    today = datetime.date.today()

    availability_states[user_id] = AvailabilityState()

    await callback.message.answer(
    f"📅 <b>Выберите дату заезда</b>\n\n{month_title(today.year, today.month)}",
    reply_markup=build_month_keyboard(
        today.year,
        today.month,
        prefix="checkin",
        min_date=today,  # 🔥 ВАЖНО
    ),
)


@router.callback_query(lambda c: c.data and c.data.startswith("checkin_month:"))
async def change_checkin_month(callback: CallbackQuery):
    if callback.data is None or callback.message is None:
        return

    _, value = callback.data.split(":")
    year, month = map(int, value.split("-"))

    await callback.message.answer(
        f"📅 <b>Выберите дату заезда</b>\n\n{month_title(year, month)}",
        reply_markup=build_month_keyboard(
            year,
            month,
            prefix="checkin",
        ),
    )
