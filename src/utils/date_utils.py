from calendar import monthrange
from datetime import date, timedelta


def next_day(d: date) -> date:
    """Return the next calendar day after the given date."""
    return d + timedelta(days=1)


def dates_in_month(year: int, month: int) -> list[date]:
    days_in_month = monthrange(year, month)[1]
    return [date(year, month, day) for day in range(1, days_in_month + 1)]


def build_import_date(year: int, month: int, day: int) -> date:
    """Build a date from imported year/month/day values with validation."""
    if not isinstance(year, int):
        raise ValueError("Import config 'year' must be an integer")
    if not isinstance(month, int):
        raise ValueError("Import config 'month' must be an integer")
    if month < 1 or month > 12:
        raise ValueError("Import config 'month' must be between 1 and 12")
    if not isinstance(day, int):
        raise ValueError("Day value must be an integer")

    try:
        return date(year, month, day)
    except ValueError as exc:
        raise ValueError(f"Invalid day '{day}' for {year:04d}-{month:02d}") from exc
