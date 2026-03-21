from datetime import date

try:
    from constraints.violation import ConstraintSeverity as Severity
    from constraints.violation import collector, constraint
    from model.schedule import Schedule
    from model.shift import Shift
    from model.shift_type import ShiftWorkType
    from utils.date_utils import dates_in_month, next_day
except ModuleNotFoundError:
    from src.constraints.violation import ConstraintSeverity as Severity
    from src.constraints.violation import collector, constraint
    from src.model.schedule import Schedule
    from src.model.shift import Shift
    from src.utils.date_utils import dates_in_month, next_day


@constraint("Five Consecutive Shifts")
def five_consecutive_shifts(schedule: Schedule) -> bool:
    """Ensure that no worker has more than 5 consecutive shifts.
    Returns True if any worker has more than 5 consecutive shifts, else False."""
    constraint_broken = False

    def break_constraint(worker_id: int, shifts: list[Shift]) -> None:
        nonlocal constraint_broken
        worker = schedule.get_worker(worker_id)
        collector.add_current(
            severity=Severity.ERROR,
            message=f"Worker {worker.name} has more than 5 consecutive shifts.",
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

    class WorkingWeekend:
        days: tuple[date, date]
        status: str = "unknown"  # "working", "off", "half-off" or "unknown"

        def __init__(self, days: tuple[date, date]):
            self.days = days

        def register_shift(self, shift: Shift) -> None:
            if self.unknown():
                if shift.is_work_shift():
                    self.status = "working"
                else:
                    self.status = "half-off"
            elif self._half_off() and not shift.is_work_shift():
                self.status = "off"
            else:
                self.status = "working"

        def unknown(self) -> bool:
            return self.status == "unknown"

        def working(self) -> bool:
            return self.status == "working"

        def _half_off(self) -> bool:
            return self.status == "half-off"

    class WorkingWeekendMonth:
        weekends: list[WorkingWeekend] = []
        map_weekend: dict[date, int] = {}  # Map from date to index of weekend
        month_days: list[date]

        def __init__(self, year: int, month: int):
            self.month_days = dates_in_month(year, month)
            # Exclude the last day to avoid broken weekend
            for day in self.month_days[:-1]:
                if day.weekday() == 5:  # Saturday
                    sunday = next_day(day)
                    self.weekends.append(WorkingWeekend(days=(day, sunday)))
                    index = len(self.weekends) - 1
                    self.map_weekend[day] = index
                    self.map_weekend[sunday] = index

        def register_shift(self, shift: Shift) -> None:
            weekend = self._get_weekend(shift.date)
            weekend.register_shift(shift)

        def _get_weekend(self, date: date) -> WorkingWeekend:
            self._validate_weekend_date(date)
            weekend_index = self.map_weekend[date]
            return self.weekends[weekend_index]

        def _validate_weekend_date(self, date: date) -> None:
            if date not in self.map_weekend:
                raise ValueError(f"Date {date} is not a weekend day in this month.")

    def break_constraint(worker_id: int, month_key: tuple[int, int]) -> None:
        nonlocal constraint_broken
        worker = schedule.get_worker(worker_id)
        collector.add_current(
            severity=Severity.ERROR,
            message=(
                f"Worker {worker.name} has no full weekend off in "
                f"{month_key[0]}-{month_key[1]:02d}."
            ),
            worker_id=worker_id,
            details={"month": f"{month_key[0]}-{month_key[1]:02d}"},
        )
        constraint_broken = True

    def issue_warning(worker_id: int, ww: WorkingWeekend) -> None:
        worker = schedule.get_worker(worker_id)
        collector.add_current(
            severity=Severity.WARNING,
            message=(
                f"Missing weekend shift data for worker {worker.name} in "
                f"{ww.days[0].isoformat()} - {ww.days[1].isoformat()}. "
                "Working weekend constraint not applied for this month for this worker."
            ),
            worker_id=worker_id,
            details={
                "missing_weekend": [d.isoformat() for d in ww.days],
                "worker_id": worker_id,
            },
        )

    for worker_id, shifts in schedule.shifts_by_worker.items():
        # Group shifts by month
        shifts_by_month: dict[tuple[int, int], list[Shift]] = {}
        for shift in shifts:
            month_key = (shift.date.year, shift.date.month)
            shifts_by_month.setdefault(month_key, []).append(shift)

        for (year, month), month_shifts in shifts_by_month.items():
            wwk_month = WorkingWeekendMonth(year, month)

            for shift in month_shifts:
                if shift.date in wwk_month.map_weekend:
                    wwk_month.register_shift(shift)

            # Working every weekend
            if all(ww.working() for ww in wwk_month.weekends):
                break_constraint(worker_id, (year, month))

            # Weekend missing
            for ww in wwk_month.weekends:
                if ww.unknown():
                    issue_warning(worker_id, ww)

    return constraint_broken


@constraint("Rest Gap")
def rest_gap(schedule: Schedule) -> bool:
    """Ensure that there is at least 11 hours of rest between shifts for each worker.
    Returns True if any worker has less than 11 hours between shifts, else False."""
    constraint_broken = False

    def break_constraint(
        worker_id: int, prev_shift: Shift, curr_shift: Shift, hours_between: int
    ) -> None:
        nonlocal constraint_broken
        worker = schedule.get_worker(worker_id)
        collector.add_current(
            severity=Severity.ERROR,
            message=(
                f"Worker {worker.name} has only {hours_between} hours of rest between "
                f"{prev_shift.to_string()} and {curr_shift.to_string()}."
            ),
            worker_id=worker_id,
            details={
                "previous_shift": prev_shift.__repr__(),
                "current_shift": curr_shift.__repr__(),
                "hours_between": hours_between,
            },
        )
        constraint_broken = True

    REST_GAP = 11
    for worker_id, shifts in schedule.shifts_by_worker.items():
        # Sort shifts by date to check for rest gaps
        sorted_shifts = sorted(shifts, key=lambda s: s.date)
        for i in range(1, len(sorted_shifts)):
            prev_shift = sorted_shifts[i - 1]
            curr_shift = sorted_shifts[i]
            if prev_shift.is_work_shift() and curr_shift.is_work_shift():
                prev_end_hour = prev_shift.shift_type.hours_range()[1]
                curr_start_hour = curr_shift.shift_type.hours_range()[0]
                hours_between = (curr_shift.date - prev_shift.date).days * 24 + (
                    curr_start_hour - prev_end_hour
                )
                if hours_between < REST_GAP:
                    break_constraint(worker_id, prev_shift, curr_shift, hours_between)

    return constraint_broken