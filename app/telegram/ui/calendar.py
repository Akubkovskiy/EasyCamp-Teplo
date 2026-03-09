import datetime
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.domain.calendar import get_month_dates

MONTHS_RU = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
]


def month_title(year: int, month: int) -> str:
    return f"{MONTHS_RU[month - 1]} {year}"


def build_month_keyboard(
    year: int,
    month: int,
    prefix: str,
    min_date: datetime.date | None = None,
    back_callback: str = "admin:menu",
) -> InlineKeyboardMarkup:
    today = datetime.date.today()
    dates = get_month_dates(year, month)

    keyboard: list[list[InlineKeyboardButton]] = []

    # 1. Заголовок (кликабельный месяц)
    keyboard.append(
        [
            InlineKeyboardButton(
                text=month_title(year, month),
                callback_data=f"{prefix}_pick_month:{year}",
            )
        ]
    )

    # 2. Дни недели
    week_days = ["Пн", "Вт", "Ср", " Чт", "Пт", "Сб", "Вс"]
    keyboard.append(
        [InlineKeyboardButton(text=day, callback_data="ignore") for day in week_days]
    )

    # 3. Дни месяца
    row: list[InlineKeyboardButton] = []
    for date in dates:
        # ⛔ Отсекаем даты раньше min_date (если задан)
        if min_date and date < min_date:
            row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        else:
            label = str(date.day) if date != today else f"🔹 {date.day}"
            row.append(
                InlineKeyboardButton(
                    text=label, callback_data=f"{prefix}:{date.isoformat()}"
                )
            )

        if len(row) == 7:
            keyboard.append(row)
            row = []

    if row:
        # Добиваем пустками если ряд не полный
        while len(row) < 7:
            row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        keyboard.append(row)

    # 4. Навигация
    prev_month = (datetime.date(year, month, 1) - datetime.timedelta(days=1)).replace(
        day=1
    )
    next_month = (datetime.date(year, month, 28) + datetime.timedelta(days=4)).replace(
        day=1
    )

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

    # 5. Кнопка Назад
    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔙 Назад в меню",
                callback_data=back_callback,
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_year_keyboard(year: int, prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора месяца"""
    keyboard = []

    # Заголовок года
    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️", callback_data=f"{prefix}_pick_year:{year - 1}"
            ),
            InlineKeyboardButton(text=f"{year}", callback_data="ignore"),
            InlineKeyboardButton(
                text="➡️", callback_data=f"{prefix}_pick_year:{year + 1}"
            ),
        ]
    )

    # Месяцы сеткой 3x4
    row = []
    for i, m_name in enumerate(MONTHS_RU):
        row.append(
            InlineKeyboardButton(
                text=m_name, callback_data=f"{prefix}_month:{year}-{i + 1}"
            )
        )
        if len(row) == 3:
            keyboard.append(row)
            row = []

    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔙 Отмена", callback_data=f"{prefix}_month:{year}-1"
            )
        ]
    )  # Вернет в Январь (или текущий, сложнее прокинуть)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
