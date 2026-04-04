from src.constraints.violation import ConstraintSeverity as Severity
from src.constraints.violation import collector, constraint_meta, hard_constraint
from src.model.schedule import Schedule
from src.model.shift import Shift
from src.utils.errors.error_handler import ErrorHandler as Error


@hard_constraint
@constraint_meta(
    "Five Consecutive Shifts",
    "Ensure that no worker has more than 5 consecutive shifts in a row. Violations are severe and will be reported as errors.",
)
def five_consecutive_shifts(schedule: Schedule) -> bool:
    """Ensure that no worker has more than 5 consecutive shifts in a row.
    Returns True if any worker has more than 5 consecutive shifts, else False."""
    constraint_broken = False

    def break_constraint(worker_id: int, shifts: list[Shift]) -> None:
        nonlocal constraint_broken
        worker = schedule.get_worker(worker_id)
        if worker is None:
            raise ValueError(
                Error.get_message("errors.worker_not_found", worker_id=worker_id)
            )
        collector.add_current(
            severity=Severity.ERROR,
            message=Error.get_message(
                "constraints.hard.consecutive_shifts", worker=worker
            ),
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


@hard_constraint
@constraint_meta(
    "Rest Gap",
    "Ensure that there is at least 11 hours of rest between shifts for each worker. "
    "Violations are severe and will be reported as errors.",
)
def rest_gap(schedule: Schedule) -> bool:
    """Ensure that there is at least 11 hours of rest between shifts for each worker.
    Returns True if any worker has less than 11 hours between shifts, else False."""
    constraint_broken = False

    def break_constraint(
        worker_id: int, prev_shift: Shift, curr_shift: Shift, hours_between: int
    ) -> None:
        nonlocal constraint_broken
        worker = schedule.get_worker(worker_id)
        if worker is None:
            raise ValueError(
                Error.get_message("errors.worker_not_found", worker_id=worker_id)
            )
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