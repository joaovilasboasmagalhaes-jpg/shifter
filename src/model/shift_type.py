from enum import Enum
from typing import Tuple


class ShiftType(Enum):
    """Base enum for shift categories.

    This provides a common base type for more specific shift enums
    (`ShiftWorkType`, `ShiftBreakType`) and declares the common
    interface expected by consumers (e.g. `to_string`).
    """

    def to_string(self) -> str:
        """Return a human-readable label for the shift type.

        Sub-classes (enum members defined on subclasses) should override
        this. We raise NotImplementedError here to make the contract clear
        to static type checkers.
        """
        raise NotImplementedError()


class ShiftWorkType(ShiftType):
    """Work shift types with an associated hour range.

    Members:
        NIGHT: 00:00-08:00
        MORNING: 08:00-16:00
        AFTERNOON: 16:00-24:00
    """

    NIGHT = (0, "Night", (0, 8))
    MORNING = (1, "Morning", (8, 16))
    AFTERNOON = (2, "Afternoon", (16, 24))

    def __init__(self, code: int, label: str, hours: Tuple[int, int]):
        self.code = code
        self.label = label
        self.hours = hours

    def to_string(self) -> str:
        """Return a human-readable label for the shift."""
        return self.label

    def hours_range(self) -> Tuple[int, int]:
        """Return the (start_hour, end_hour) tuple in 24-hour integers."""
        return self.hours

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.to_string()


class ShiftBreakType(ShiftType):
    """Non-working shift types (breaks/time off)."""

    DAY_OFF = (10, "DayOff")
    VACATION = (11, "Vacation")

    def __init__(self, code: int, label: str):
        self.code = code
        self.label = label

    def to_string(self) -> str:
        return self.label

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.to_string()
