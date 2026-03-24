from calendar import monthrange
from datetime import date, timedelta

from src.utils.errors.error_handler import ErrorHandler as Error


def next_day(d: date) -> date:
    """Return the next calendar day after the given date."""
    return d + timedelta(days=1)


def dates_in_month(year: int, month: int) -> list[date]:
    days_in_month = monthrange(year, month)[1]
    return [date(year, month, day) for day in range(1, days_in_month + 1)]


def build_import_date(year: int, month: int, day: int) -> date:
    """Build a date from imported year/month/day values with validation."""
    if not isinstance(year, int):
        raise ValueError(Error.get_message("errors.import_year_int"))
    if not isinstance(month, int):
        raise ValueError(Error.get_message("errors.import_month_int"))
    if month < 1 or month > 12:
        raise ValueError(Error.get_message("errors.import_month_range"))
    if not isinstance(day, int):
        raise ValueError(Error.get_message("errors.import_day_int"))

    try:
        return date(year, month, day)
    except ValueError as exc:
        raise ValueError(
            Error.get_message(
                "errors.import_day_range", day=day, year=year, month=month
            )
        ) from exc
