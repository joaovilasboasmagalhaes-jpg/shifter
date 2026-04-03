from dataclasses import dataclass, field
from datetime import date
from typing import cast

from src.model.shift import Shift
from src.model.worker import Worker
from src.utils.errors.error_handler import ErrorHandler as Error


@dataclass
class Schedule:
    """A schedule with a start and end date and a list of shifts.

    Methods:
        add_shift(shift): add a Shift if it's within the schedule range, else raise ValueError
        shifts_on(d): return list of shifts on date d
        shifts_for_worker(worker_id): return list of shifts assigned to the worker id
    """

    start_date: date
    end_date: date
    shifts_by_worker: dict[int, list[Shift]] = field(
        default_factory=lambda: cast(dict[int, list[Shift]], {})
    )

    def add_shift(self, shift: Shift) -> None:
        """Add a shift if its date is within the schedule range.

        Raises ValueError if the shift date is outside the inclusive range.
        """
        if not self.is_date_within_range(shift.date):
            raise ValueError(
                Error.get_message("errors.shift_date_out_of_range", date=shift.date)
            )
        self.shifts_by_worker.setdefault(shift.worker.id, []).append(shift)

    def get_shift(self, worker_id: int, shift_date: date) -> Shift | None:
        """Return the shift for a given worker and date, or None if not found."""
        worker_shifts = self.shifts_by_worker.get(worker_id, [])
        for shift in worker_shifts:
            if shift.date == shift_date:
                return shift
        return None

    def shifts_on(self, d: date) -> list[Shift]:
        """Return all shifts scheduled on date `d`."""
        if not self.is_date_within_range(d):
            return []
        return [
            shift
            for worker_shifts in self.shifts_by_worker.values()
            for shift in worker_shifts
            if shift.date == d
        ]

    def get_worker(self, worker_id: int) -> Worker | None:
        """Return the Worker object for a given worker id, or None if not found."""
        worker_shifts = self.shifts_by_worker.get(worker_id)
        if not worker_shifts:
            return None
        return worker_shifts[0].worker

    def shifts_for_worker(self, worker_id: int) -> list[Shift]:
        """Return all shifts assigned to a worker id."""
        return list(self.shifts_by_worker.get(worker_id, []))

    def is_date_within_range(self, d: date) -> bool:
        """Check if a date is within the schedule's start and end dates."""
        return self.start_date <= d <= self.end_date

    def to_string(self) -> str:
        total_shifts = sum(
            len(worker_shifts) for worker_shifts in self.shifts_by_worker.values()
        )
        return f"Schedule {self.start_date.isoformat()} to {self.end_date.isoformat()} ({total_shifts} shifts)"

    def __str__(self) -> str:
        return self.to_string()
