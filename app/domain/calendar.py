import calendar
import datetime


def get_month_dates(year: int, month: int) -> list[datetime.date]:
    _, days_in_month = calendar.monthrange(year, month)
    return [
        datetime.date(year, month, day)
        for day in range(1, days_in_month + 1)
    ]
