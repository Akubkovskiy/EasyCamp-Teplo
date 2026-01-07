import datetime
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.domain.calendar import get_month_dates

MONTHS_RU = [
    "Январь", "Февраль", "Март", "Апрель",
    "Май", "Июнь", "Июль", "Август",
    "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]


def build_month_keyboard(
    year: int,
    month: int,
    prefix: str,
    min_date: datetime.date | None = None,
) -> InlineKeyboardMarkup:
    today = datetime.date.today()
    dates = get_month_dates(year, month)

    keyboard: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for date in dates:
        # ⛔ Отсекаем даты раньше min_date (если задан)
        if min_date and date < min_date:
            continue

        label = str(date.day)

        if date == today:
            label = f"🔹 {label}"

        row.append(
            InlineKeyboardButton(
                text=label,
                callback_data=f"{prefix}:{date.isoformat()}",
            )
        )

        if len(row) == 7:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Навигация по месяцам
    prev_month = (datetime.date(year, month, 1) - datetime.timedelta(days=1)).replace(day=1)
    next_month = (datetime.date(year, month, 28) + datetime.timedelta(days=4)).replace(day=1)

    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"{prefix}_month:{prev_month.year}-{prev_month.month}",
            ),
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"{prefix}_month:{next_month.year}-{next_month.month}",
            ),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад в меню",
                callback_data="admin:menu",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def month_title(year: int, month: int) -> str:
    return f"{MONTHS_RU[month - 1]} {year}"
