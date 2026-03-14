from dataclasses import dataclass, field
from datetime import date
from typing import List

from src.model.shift import Shift


@dataclass
class Schedule:
    """A schedule with a start and end date and a list of shifts.

    Methods:
        add_shift(shift): add a Shift if it's within the schedule range, else raise ValueError
        shifts_on(d): return list of shifts on date d
    """

    start_date: date
    end_date: date
    shifts: List[Shift] = field(default_factory=list)

    def add_shift(self, shift: Shift) -> None:
        """Add a shift if its date is within the schedule range.

        Raises ValueError if the shift date is outside the inclusive range.
        """
        if not self.is_date_within_range(shift.date):
            raise ValueError("Shift date out of schedule range")
        self.shifts.append(shift)

    def shifts_on(self, d: date) -> List[Shift]:
        """Return all shifts scheduled on date `d`."""
        if not self.is_date_within_range(d):
            raise ValueError("Date is out of schedule range")
        return [s for s in self.shifts if s.date == d]
    
    def is_date_within_range(self, d: date) -> bool:
        """Check if a date is within the schedule's start and end dates."""
        return self.start_date <= d <= self.end_date

    def to_string(self) -> str:
        return f"Schedule {self.start_date.isoformat()} to {self.end_date.isoformat()} ({len(self.shifts)} shifts)"

    def __str__(self) -> str:
        return self.to_string()
