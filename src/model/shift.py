from dataclasses import dataclass
from datetime import date

try:
    from model.shift_type import ShiftType
    from model.worker import Worker
except ModuleNotFoundError:
    from src.model.shift_type import ShiftType
    from src.model.worker import Worker


@dataclass
class Shift:
    """Represents a scheduled shift for a worker.

    Attributes:
        shift_type: One of `ShiftWorkType` or `ShiftBreakType`.
        date: The date of the shift (datetime.date).
        worker: The `Worker` assigned to the shift.
    """

    shift_type: ShiftType
    date: date
    worker: Worker

    def consecutive_shifts(self, other: "Shift") -> bool:
        """Return True if this shift and the other shift are on consecutive days."""
        return abs((self.date - other.date).days) == 1

    def is_work_shift(self) -> bool:
        """Return True if this shift is a work shift, False if it's a break."""
        return self.shift_type.is_work_shift()

    def to_string(self) -> str:
        """Return a human-readable representation of the shift."""
        # Use the shift_type's label (via to_string), ISO date and worker name.
        return f"{self.shift_type.to_string()} on {self.date.isoformat()} - {self.worker.name}"

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Shift('{self.shift_type.get_short_label()}', {self.worker.name}, '{self.date.isoformat()}')"