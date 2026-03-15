from enum import Enum
from typing import Optional, Tuple


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

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return str(getattr(self, "short_label", self.to_string()))

    @classmethod
    def from_short_label(
        cls, short_label: str, config: Optional[dict[str, str]] = None
    ) -> "ShiftType":
        """Resolve a shift type by short label across all concrete shift enums."""

        for enum_cls in (ShiftWorkType, ShiftBreakType):
            try:
                return enum_cls.from_short_label(short_label, config)
            except ValueError:
                continue

        raise ValueError(f"Unknown shift short label: {short_label}")


class ShiftWorkType(ShiftType):
    """Work shift types with an associated hour range.

    Members:
        NIGHT: 00:00-08:00
        MORNING: 08:00-16:00
        AFTERNOON: 16:00-24:00
    """

    NIGHT = (0, "Night", "N", (0, 8), "night")
    MORNING = (1, "Morning", "M", (8, 16), "morning")
    AFTERNOON = (2, "Afternoon", "A", (16, 24), "afternoon")

    def __init__(
        self,
        code: int,
        label: str,
        og_short_label: str,
        hours: Tuple[int, int],
        config_label: str,
    ):
        self.code = code
        self.label = label
        self.og_short_label = og_short_label
        self.short_label = og_short_label
        self.hours = hours
        self.config_label = config_label

    def to_string(self) -> str:
        """Return a human-readable label for the shift."""
        return self.label

    @classmethod
    def from_short_label(
        cls, short_label: str, config: Optional[dict[str, str]] = None
    ) -> "ShiftWorkType":
        """Resolve a work shift by short label."""
        config = config or {}
        for shift_type in cls:
            shift_type.short_label = config.get(
                shift_type.config_label, shift_type.og_short_label
            )
            if shift_type.short_label == short_label:
                return shift_type
        raise ValueError(f"Unknown work shift short label: {short_label}")

    def hours_range(self) -> Tuple[int, int]:
        """Return the (start_hour, end_hour) tuple in 24-hour integers."""
        return self.hours

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.to_string()


class ShiftBreakType(ShiftType):
    """Non-working shift types (breaks/time off)."""

    DAY_OFF = (10, "DayOff", "DO", "day_off")
    VACATION = (11, "Vacation", "V", "vacation")

    def __init__(self, code: int, label: str, og_short_label: str, config_label: str):
        self.code = code
        self.label = label
        self.og_short_label = og_short_label
        self.short_label = og_short_label
        self.config_label = config_label

    def to_string(self) -> str:
        return self.label

    @classmethod
    def from_short_label(
        cls, short_label: str, config: Optional[dict[str, str]] = None
    ) -> "ShiftBreakType":
        """Resolve a break shift by short label."""
        config = config or {}
        for shift_type in cls:
            shift_type.short_label = config.get(
                shift_type.config_label, shift_type.og_short_label
            )
            if shift_type.short_label == short_label:
                return shift_type
        raise ValueError(f"Unknown break shift short label: {short_label}")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.to_string()
