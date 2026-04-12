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
from src.model.worker import Worker
from src.utils.errors.error_handler import ErrorHandler as Error


class ConstraintDisplay:
    title: str
    description: str
    workers: list[Worker] = []
    violations: list[ConstraintViolation]

    def __init__(
        self,
        title: str,
        description: str,
        violations: Optional[list[ConstraintViolation]] = None,
        schedule: Optional[Schedule] = None,
        workers: Optional[list[Worker]] = None,
    ):
        self.title = title
        self.description = description
        self.violations = violations if violations is not None else []
        self._build_workers(schedule, workers)

    def _build_workers(
        self,
        schedule: Optional[Schedule] = None,
        workers: Optional[list[Worker]] = None,
    ):
        if workers is not None:
            self.workers = workers
        elif schedule is not None:
            self.workers = schedule.get_workers()
        else:
            raise ValueError(
                Error.get_message("system_errors.schedule_or_workers_required")
            )


class HardConstraintDisplay(ConstraintDisplay):
    broken: bool = False

    def __init__(
        self,
        title: str,
        description: str,
        broken: bool = False,
        violations: Optional[list[ConstraintViolation]] = None,
        schedule: Optional[Schedule] = None,
        workers: Optional[list[Worker]] = None,
    ):
        super().__init__(title, description, violations, schedule, workers)
        self.broken = broken

    def __repr__(self) -> str:
        status = "Broken" if self.broken else "Satisfied"
        return f"{self.title}: {status}"


class SoftConstraintDisplay(ConstraintDisplay):
    score: float = 0.0
    per_worker_scores: dict[int, float] = {}

    def __init__(
        self,
        title: str,
        description: str,
        score: float = 0.0,
        per_worker_scores: dict[int, float] = {},
        violations: Optional[list[ConstraintViolation]] = None,
        schedule: Optional[Schedule] = None,
        workers: Optional[list[Worker]] = None,
    ):
        super().__init__(title, description, violations, schedule, workers)
        self.score = score
        self.per_worker_scores = per_worker_scores

    def get_worker_scores(self) -> dict[str, float]:
        return {
            worker.to_string(): self.per_worker_scores.get(worker.id, 0.0)
            for worker in self.workers
        }

    def __str__(self) -> str:
        return f"{self.title}: Score={self.score:.2f} | {self.description}"

    def __repr__(self) -> str:
        return f"{self.title}: Score={self.score:.2f}"


def _run_hard_constraints(schedule: Schedule) -> dict[str, HardConstraintDisplay]:
    hard_constraints: dict[str, HardConstraintDisplay] = {}

    def run_constraint(constraint_fn: Constraint, schedule: Schedule, **kwargs):
        """Helper function to run a hard constraint and record its result."""
        broken = constraint_fn(schedule, **kwargs)
        hard_constraints[constraint_fn.title] = HardConstraintDisplay(
            title=constraint_fn.title,
            description=constraint_fn.description,
            broken=broken,
            schedule=schedule,
            violations=collector.get_violations(constraint_fn),
        )

    run_constraint(five_consecutive_shifts, schedule=schedule)
    run_constraint(rest_gap, schedule=schedule)

    return hard_constraints


def _run_soft_constraints(
    schedule: Schedule, preferences: Optional[Schedule] = None
) -> dict[str, SoftConstraintDisplay]:
    soft_constraints: dict[str, SoftConstraintDisplay] = {}

    def run_constraint(constraint_fn: Constraint, schedule: Schedule, **kwargs):
        """Helper function to run a soft constraint and record its result."""
        score, per_worker_scores = constraint_fn(schedule, **kwargs)
        soft_constraints[constraint_fn.title] = SoftConstraintDisplay(
            title=constraint_fn.title,
            description=constraint_fn.description,
            score=score,
            per_worker_scores=per_worker_scores,
            schedule=schedule,
            violations=collector.get_violations(constraint_fn),
        )

    run_constraint(balanced_schedule, schedule=schedule)
    run_constraint(shift_continuation, schedule=schedule)
    if preferences is not None:
        run_constraint(preferred_schedule, schedule=schedule, preferences=preferences)
    run_constraint(monthly_weekend, schedule=schedule)

    return soft_constraints


def evaluate(
    schedule: Schedule, preferences: Optional[Schedule] = None
) -> tuple[dict[str, HardConstraintDisplay], dict[str, SoftConstraintDisplay]]:
    hard_constraints = _run_hard_constraints(schedule)
    soft_constraints = _run_soft_constraints(schedule, preferences)
    collector.clear()
    return hard_constraints, soft_constraints