from enum import Enum
from typing import Tuple

from src.model.config import Config
from src.utils.errors.error_handler import ErrorHandler as Error


class ShiftType(Enum):
    """Base enum for shift categories.

    This provides a common base type for more specific shift enums
    (`ShiftWorkType`, `ShiftBreakType`) and declares the common
    interface expected by consumers (e.g. `to_string`).
    """

    def __init__(
        self,
        code: int,
        label: str,
        short_label: str,
        hours: Tuple[int, int] | None,
        config_label: str,
    ):
        self.code = code
        self.label = label
        self.short_label = short_label
        self.hours = hours
        self.config_label = config_label

    def is_work_shift(self) -> bool:
        """Return True if this shift type is a work shift, False if it's a break."""
        return isinstance(self, ShiftWorkType)

    def get_short_label(self) -> str:
        """Return the default short label for this shift type."""
        return self._effective_short_label()

    def hours_range(self) -> Tuple[int, int]:
        """Return the (start_hour, end_hour) tuple in 24-hour integers.

        Raises:
            ValueError: If this shift type does not have defined hours.
        """
        if self.hours is None:
            raise ValueError(
                Error.get_message("errors.shift_type_no_hours", name=self.name)
            )
        return self.hours

    def to_string(self) -> str:
        """Return the human-readable label for this shift type."""
        return str(getattr(self, "label", self.name))

    @classmethod
    def _configured_short_labels(cls) -> dict[str, str]:
        """Return shift-type short-label overrides from the runtime Config singleton."""
        try:
            return Config.get_instance().shift_type_labels
        except RuntimeError:
            return {}

    def _effective_short_label(self) -> str:
        """Return the configured short label, falling back to the member default."""
        config = self._configured_short_labels()
        return config.get(
            getattr(self, "config_label", ""), getattr(self, "short_label", self.name)
        )

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return self._effective_short_label()

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.to_string()

    @classmethod
    def from_short_label(cls, short_label: str) -> "ShiftType":
        """Resolve a shift type by short label.

        - Called on ShiftType: searches all concrete shift enums.
        - Called on a concrete enum class: searches only that enum.
        """
        if cls is ShiftType:
            for enum_cls in (ShiftWorkType, ShiftBreakType):
                try:
                    return enum_cls.from_short_label(short_label)
                except ValueError:
                    continue
            raise ValueError(
                Error.get_message(
                    "errors.unknown_shift_short_label", short_label=short_label
                )
            )

        for member in cls:
            configured_label = member._effective_short_label()
            default_label = getattr(member, "short_label", member.name)
            if short_label == configured_label or short_label == default_label:
                return member

        raise ValueError(
            Error.get_message(
                "errors.unknown_class_short_label",
                class_name=cls.__name__,
                short_label=short_label,
            )
        )


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

class ShiftBreakType(ShiftType):
    """Non-working shift types (breaks/time off)."""

    DAY_OFF = (10, "DayOff", "DO", None, "day_off")
    VACATION = (11, "Vacation", "V", None, "vacation")

