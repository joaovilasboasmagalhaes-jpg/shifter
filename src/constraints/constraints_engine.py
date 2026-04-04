from typing import Optional

from src.constraints.hard import five_consecutive_shifts, rest_gap
from src.constraints.soft import (
    balanced_schedule,
    monthly_weekend,
    preferred_schedule,
    shift_continuation,
)
from src.constraints.violation import Constraint, ConstraintViolation, collector
from src.model.schedule import Schedule


class ConstraintDisplay:
    title: str
    description: str
    violations: list[ConstraintViolation]

    def __init__(
        self,
        title: str,
        description: str,
        violations: Optional[list[ConstraintViolation]] = None,
    ):
        self.title = title
        self.description = description
        self.violations = violations if violations is not None else []


class HardConstraintDisplay(ConstraintDisplay):
    broken: bool = False

    def __init__(
        self,
        title: str,
        description: str,
        broken: bool = False,
        violations: Optional[list[ConstraintViolation]] = None,
    ):
        super().__init__(title, description, violations)
        self.broken = broken

    def __repr__(self) -> str:
        status = "Broken" if self.broken else "Satisfied"
        return f"{self.title}: {status}"


class SoftConstraintDisplay(ConstraintDisplay):
    score: float = 0.0

    def __init__(
        self,
        title: str,
        description: str,
        score: float = 0.0,
        violations: Optional[list[ConstraintViolation]] = None,
    ):
        super().__init__(title, description, violations)
        self.score = score

    def __repr__(self) -> str:
        return f"{self.title}: Score={self.score:.2f}"


def _run_hard_constraints(schedule: Schedule) -> list[HardConstraintDisplay]:
    hard_constraints: list[HardConstraintDisplay] = []

    def run_constraint(constraint_fn: Constraint, schedule: Schedule, **kwargs):
        """Helper function to run a hard constraint and record its result."""
        broken = constraint_fn(schedule, **kwargs)
        hard_constraints.append(
            HardConstraintDisplay(
                title=constraint_fn.title,
                description=constraint_fn.description,
                broken=broken,
                violations=collector.get_violations(constraint_fn),
            )
        )

    run_constraint(five_consecutive_shifts, schedule=schedule)
    run_constraint(rest_gap, schedule=schedule)

    return hard_constraints


def _run_soft_constraints(
    schedule: Schedule, preferences: Optional[Schedule] = None
) -> list[SoftConstraintDisplay]:
    soft_constraints: list[SoftConstraintDisplay] = []

    def run_constraint(constraint_fn: Constraint, schedule: Schedule, **kwargs):
        """Helper function to run a soft constraint and record its result."""
        score = constraint_fn(schedule, **kwargs)
        soft_constraints.append(
            SoftConstraintDisplay(
                title=constraint_fn.title,
                description=constraint_fn.description,
                score=score,
                violations=collector.get_violations(constraint_fn),
            )
        )

    run_constraint(balanced_schedule, schedule=schedule)
    run_constraint(shift_continuation, schedule=schedule)
    if preferences is not None:
        run_constraint(preferred_schedule, schedule=schedule, preferences=preferences)
    run_constraint(monthly_weekend, schedule=schedule)

    return soft_constraints


def evaluate(schedule: Schedule, preferences: Optional[Schedule] = None) -> None:
    hard_constraints = _run_hard_constraints(schedule)
    soft_constraints = _run_soft_constraints(schedule, preferences)
    collector.clear()
    return