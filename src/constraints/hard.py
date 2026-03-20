from calendar import monthrange
from datetime import date

try:
    from constraints.violation import ConstraintSeverity as Severity
    from constraints.violation import collector, constraint
    from model.schedule import Schedule
    from model.shift import Shift
    from model.shift_type import ShiftWorkType
except ModuleNotFoundError:
    from src.constraints.violation import ConstraintSeverity as Severity
    from src.constraints.violation import collector, constraint
    from src.model.schedule import Schedule
    from src.model.shift import Shift
    from src.model.shift_type import ShiftWorkType


@constraint("Five Consecutive Shifts")
def five_consecutive_shifts(schedule: Schedule) -> bool:
    """Ensure that no worker has more than 5 consecutive shifts.
    Returns True if any worker has more than 5 consecutive shifts, else False."""
    constraint_broken = False

    def break_constraint(worker_id: int, shifts: list[Shift]) -> None:
        nonlocal constraint_broken
        collector.add_current(
            severity=Severity.ERROR,
            message=f"Worker {worker_id} has more than 5 consecutive shifts.",
            worker_id=worker_id,
            details={"consecutive_shifts": [s.__repr__() for s in shifts]},
        )
        constraint_broken = True

    for worker_id, shifts in schedule.shifts_by_worker.items():
        # Sort shifts by date to check for consecutive days
        sorted_shifts = sorted(shifts, key=lambda s: s.date)
        consecutive_count = 1

        for i in range(1, len(sorted_shifts)):
            if (sorted_shifts[i].date - sorted_shifts[i - 1].date).days == 1:
                consecutive_count += 1
                if consecutive_count > 5:
                    break_constraint(worker_id, sorted_shifts[i - 5 : i + 1])
            else:
                consecutive_count = 1

    return constraint_broken


@constraint("Monthly Weekend Off")
def monthly_weekend(schedule: Schedule) -> bool:
    """Ensure that each worker has at least one full weekend off per month."""
    constraint_broken = False

    def break_constraint(worker_id: int, month_key: tuple[int, int]) -> None:
        nonlocal constraint_broken
        collector.add_current(
            severity=Severity.ERROR,
            message=(
                f"Worker {worker_id} has no full weekend off in "
                f"{month_key[0]}-{month_key[1]:02d}."
            ),
            worker_id=worker_id,
            details={"month": f"{month_key[0]}-{month_key[1]:02d}"},
        )
        constraint_broken = True

    def dates_in_month(year: int, month: int) -> list[date]:
        days_in_month = monthrange(year, month)[1]
        return [date(year, month, day) for day in range(1, days_in_month + 1)]

    for worker_id, shifts in schedule.shifts_by_worker.items():
        # Group shifts by month
        shifts_by_month: dict[tuple[int, int], list[Shift]] = {}
        for shift in shifts:
            month_key = (shift.date.year, shift.date.month)
            shifts_by_month.setdefault(month_key, []).append(shift)

        for month_key, month_shifts in shifts_by_month.items():
            month_days = dates_in_month(month_key[0], month_key[1])
            weekends: list[tuple[date, date]] = []
            for day in month_days:
                if day.weekday() == 5:  # Saturday
                    sunday = date(day.year, day.month, day.day + 1)
                    weekends.append((day, sunday))

            worked_dates = {
                shift.date
                for shift in month_shifts
                if isinstance(shift.shift_type, ShiftWorkType)
            }

            worked_every_weekend = all(
                (saturday in worked_dates) or (sunday in worked_dates)
                for saturday, sunday in weekends
            )

            if weekends and worked_every_weekend:
                break_constraint(worker_id, month_key)

    return constraint_broken