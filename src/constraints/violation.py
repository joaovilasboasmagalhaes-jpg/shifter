import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TypeVar, cast

from src.utils.errors.error_handler import ErrorHandler as Error

_F = TypeVar("_F", bound=Callable)
_CONSTRAINT_DISPLAY_NAMES: dict[str, str] = {}


def constraint(name: str) -> Callable[[_F], _F]:
    """Decorator that attaches a `constraint_name` attribute to a constraint function.

    Usage::

        @constraint("five_consecutive_shifts")
        def five_consecutive_shifts(schedule): ...

        collector.add(five_consecutive_shifts.constraint_name, ...)
    """
    def decorator(fn: _F) -> _F:
        if "break_constraint" not in fn.__code__.co_varnames:
            raise ValueError(
                Error.get_message("system_errors.break_constraint_required", fn=fn)
            )
        _CONSTRAINT_DISPLAY_NAMES[fn.__name__] = name
        fn.constraint_name = name  # type: ignore[attr-defined]
        return fn
    return decorator


def get_constraint_name(fn: Callable[..., object]) -> str:
    """Return a constraint display name attached by `@constraint`, or fallback to function name."""
    return cast(str, getattr(fn, "constraint_name", fn.__name__))


class ConstraintSeverity(Enum):
    WARNING = auto()
    ERROR = auto()


@dataclass
class ConstraintViolation:
    """Records a constraint violation for later reporting or logging.

    Attributes:
        constraint_name: Name of the constraint that was broken.
        severity: WARNING or ERROR severity level.
        message: Human-readable description of the violation.
        worker_id: Optional id of the worker involved in the violation.
        details: Optional dict for any additional structured context.
        timestamp: When the violation was recorded (defaults to now).
    """

    constraint_name: str
    severity: ConstraintSeverity
    message: str
    worker_id: int | None = None
    details: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_string(self) -> str:
        parts = [f"[{self.severity.name}] {self.constraint_name}: {self.message}"]
        if self.worker_id is not None:
            parts.append(f"(worker_id={self.worker_id})")
        return " ".join(parts)

    def __str__(self) -> str:
        return self.to_string()


class ViolationCollector:
    """Collects constraint violations. Use the module-level `collector` instance
    to share violations across the application."""

    def __init__(self) -> None:
        self.violations: list[ConstraintViolation] = []

    def add(
        self,
        constraint_name: str,
        severity: ConstraintSeverity,
        message: str,
        worker_id: int | None = None,
        details: dict | None = None,
    ) -> ConstraintViolation:
        """Create a ConstraintViolation, append it to the list, and return it."""
        violation = ConstraintViolation(
            constraint_name=constraint_name,
            severity=severity,
            message=message,
            worker_id=worker_id,
            details=details or {},
        )
        self.violations.append(violation)
        return violation

    def add_current(
        self,
        severity: ConstraintSeverity,
        message: str,
        worker_id: int | None = None,
        details: dict | None = None,
    ) -> ConstraintViolation:
        """Record a violation for the calling constraint function.

        This is intended to be called from inside a `@constraint` function,
        so callers don't have to pass the constraint name explicitly.
        """
        frame = inspect.currentframe()
        constraint_name = "unknown_constraint"
        while frame := frame.f_back if frame else None:
            if frame.f_code.co_name in _CONSTRAINT_DISPLAY_NAMES:
                constraint_name = _CONSTRAINT_DISPLAY_NAMES[frame.f_code.co_name]
                break
        return self.add(
            constraint_name=constraint_name,
            severity=severity,
            message=message,
            worker_id=worker_id,
            details=details,
        )

    def clear(self) -> None:
        """Remove all recorded violations."""
        self.violations.clear()


collector = ViolationCollector()
