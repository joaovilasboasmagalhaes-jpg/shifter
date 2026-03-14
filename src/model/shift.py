from dataclasses import dataclass
from datetime import date

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

    def to_string(self) -> str:
        """Return a human-readable representation of the shift."""
        # Use the shift_type's label (via to_string), ISO date and worker name.
        return f"{self.shift_type.to_string()} on {self.date.isoformat()} - {self.worker.name}"

    def __str__(self) -> str:
        return self.to_string()
