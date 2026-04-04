import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TypeVar

from src.utils.errors.error_handler import ErrorHandler as Error

_F = TypeVar("_F", bound=Callable)


class Constraint:
    """Wrapper for constraint functions, holding metadata and the function itself."""

    def __init__(
        self, func: Callable, title: str, description: str, is_hard: bool = False
    ):
        self.func = func
        self.title = title
        self.description = description
        self.is_hard = is_hard
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

_CONSTRAINT_DISPLAY_NAMES: dict[str, str] = {}


def hard_constraint(obj):
    """Decorator for hard constraints. Requires a Constraint object from @constraint_meta.
    Sets is_hard=True and enforces 'break_constraint' presence in the function signature.
    Usage::
        @hard_constraint
        @constraint_meta("Title", "Description")
        def ...
    """
    if not isinstance(obj, Constraint):
        raise ValueError(Error.get_message("system_errors.hard_constraint_after_meta"))
    fn = obj.func
    if "break_constraint" not in fn.__code__.co_varnames:
        raise ValueError(
            Error.get_message("system_errors.break_constraint_required", fn=fn)
        )
    obj.is_hard = True
    _CONSTRAINT_DISPLAY_NAMES[obj.__name__] = obj.title
    return obj


def constraint_meta(title: str, description: str) -> Callable[[_F], Constraint]:
    """Decorator for all constraints. Wraps the function in a Constraint object with metadata."""

    def decorator(fn: _F) -> Constraint:
        if not title or not description:
            raise ValueError(
                Error.get_message("system_errors.title_and_description_required")
            )
        return Constraint(fn, title, description)
    return decorator


def get_constraint_name(obj: object) -> str:
    """Return a constraint display name from a Constraint object, or fallback to function name."""
    if isinstance(obj, Constraint):
        return obj.title
    return getattr(obj, "__name__", str(obj))


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
