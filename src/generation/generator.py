

from dataclasses import dataclass
from datetime import date
from itertools import cycle

from src.constraints.constraints_engine import (
    HardConstraintResult,
    SoftConstraintResult,
    evaluate,
)
from src.model.schedule import Schedule
from src.model.shift import Shift
from src.model.shift_type import ShiftWorkType
from src.model.worker import Worker
from src.utils.date_utils import next_day


@dataclass(frozen=True)
class GenerationSettings:
    """Configuration values controlling the generation loop.

    Attributes:
        max_cycles: Maximum number of full generation cycles to execute.
        max_no_improvement_cycles: Maximum number of consecutive cycles allowed
            without improving the best schedule found so far.
    """

    max_cycles: int = 10
    max_no_improvement_cycles: int = 3


@dataclass(frozen=True)
class ScheduleEvaluation:
    """Normalized evaluation summary used by the generator.

    Attributes:
        hard_constraints: Hard-constraint evaluation results keyed by title.
        soft_constraints: Soft-constraint evaluation results keyed by title.
        total_soft_score: Sum of all soft-constraint scores. Lower is better.
        is_valid: True when no hard constraint is broken.
    """

    hard_constraints: dict[str, HardConstraintResult]
    soft_constraints: dict[str, SoftConstraintResult]
    total_soft_score: float
    is_valid: bool


@dataclass
class GenerationState:
    """Mutable snapshot of the generator progress.

    Attributes:
        current_schedule: Schedule used as the starting point for the next cycle.
        best_schedule: Best schedule found so far according to the evaluation rules.
        best_evaluation: Evaluation result associated with best_schedule.
        cycle_index: Number of completed generation cycles.
        no_improvement_cycles: Consecutive cycles that did not improve best_schedule.
    """

    current_schedule: Schedule
    best_schedule: Schedule
    best_evaluation: ScheduleEvaluation
    cycle_index: int = 0
    no_improvement_cycles: int = 0


class ScheduleGenerator:
    """High-level orchestration for the schedule generation lifecycle.

    This class defines the generation loop and delegates each stage of the
    algorithm to focused helper methods. Concrete generation logic can be added
    incrementally by implementing the placeholder methods without changing the
    outer control flow.
    """

    def __init__(self, settings: GenerationSettings | None = None):
        """Create a generator with optional runtime settings.

        Args:
            settings: Optional loop-control configuration. If omitted, defaults
                are used.
        """
        self.settings = settings or GenerationSettings()

    def generate(
        self, workers: list[Worker], start_date: date, end_date: date
    ) -> Schedule:
        """Generate and return the best schedule found for the requested period.

        The method initializes generator state, runs repeated generation cycles,
        evaluates each candidate schedule, and returns the best schedule found.

        Args:
            workers: Workers that must be considered when constructing the
                schedule.
            start_date: Inclusive first date of the scheduling window.
            end_date: Inclusive last date of the scheduling window.

        Returns:
            The best schedule produced within the configured generation limits.
        """
        state = self._initialize_generation_state(workers, start_date, end_date)

        while self._should_continue(state):
            candidate_schedule = self._run_generation_cycle(
                workers=workers,
                current_schedule=state.current_schedule,
            )
            candidate_evaluation = self._evaluate_schedule(candidate_schedule)
            state = self._advance_generation_state(
                state=state,
                candidate_schedule=candidate_schedule,
                candidate_evaluation=candidate_evaluation,
            )

        return state.best_schedule

    def _initialize_generation_state(
        self, workers: list[Worker], start_date: date, end_date: date
    ) -> GenerationState:
        """Build the initial generation state before the iterative loop starts.

        Intended logic:
            1. Construct an initial schedule for the requested period.
            2. Evaluate that schedule once.
            3. Use it as both the current and best known schedule.

        Args:
            workers: Workers available for assignment.
            start_date: Inclusive first date of the scheduling window.
            end_date: Inclusive last date of the scheduling window.

        Returns:
            A fully initialized GenerationState ready for the first cycle.
        """
        initial_schedule = self._build_initial_schedule(
            workers=workers,
            start_date=start_date,
            end_date=end_date,
        )
        initial_evaluation = self._evaluate_schedule(initial_schedule)
        return GenerationState(
            current_schedule=initial_schedule,
            best_schedule=initial_schedule,
            best_evaluation=initial_evaluation,
        )

    def _run_generation_cycle(
        self, workers: list[Worker], current_schedule: Schedule
    ) -> Schedule:
        """Produce the next candidate schedule from the current schedule.

        Intended logic:
            1. Build a candidate derived from the current schedule.
            2. Repair known hard-constraint problems if the candidate is invalid.
            3. Improve the repaired candidate to reduce soft-constraint score.

        Args:
            workers: Workers available for assignment changes.
            current_schedule: Schedule that serves as the cycle input.

        Returns:
            The candidate schedule produced for this cycle.
        """
        candidate_schedule = self._build_candidate_schedule(
            workers=workers,
            current_schedule=current_schedule,
        )
        candidate_schedule = self._repair_candidate_schedule(candidate_schedule)
        candidate_schedule = self._improve_candidate_schedule(candidate_schedule)
        return candidate_schedule

    def _evaluate_schedule(self, schedule: Schedule) -> ScheduleEvaluation:
        """Evaluate a schedule and normalize the result for generator decisions.

        Args:
            schedule: Schedule to evaluate against all active constraints.

        Returns:
            A ScheduleEvaluation containing hard-constraint status, soft scores,
            and an aggregate soft score used for candidate comparison.
        """
        hard_constraints, soft_constraints = evaluate(schedule)
        total_soft_score = sum(
            constraint.score for constraint in soft_constraints.values()
        )
        is_valid = all(
            not constraint.broken for constraint in hard_constraints.values()
        )
        return ScheduleEvaluation(
            hard_constraints=hard_constraints,
            soft_constraints=soft_constraints,
            total_soft_score=total_soft_score,
            is_valid=is_valid,
        )

    def _advance_generation_state(
        self,
        state: GenerationState,
        candidate_schedule: Schedule,
        candidate_evaluation: ScheduleEvaluation,
    ) -> GenerationState:
        """Update generation state after evaluating a cycle candidate.

        Intended logic:
            1. Compare the candidate with the best known result.
            2. Replace the best schedule if the candidate is better.
            3. Advance counters used by the stop conditions.

        Args:
            state: Current generation state before processing the candidate.
            candidate_schedule: Schedule produced in the latest cycle.
            candidate_evaluation: Evaluation of candidate_schedule.

        Returns:
            A new GenerationState reflecting the completed cycle.
        """
        improved = self._is_better_candidate(
            candidate_evaluation=candidate_evaluation,
            best_evaluation=state.best_evaluation,
        )

        best_schedule = state.best_schedule
        best_evaluation = state.best_evaluation
        no_improvement_cycles = state.no_improvement_cycles + 1

        if improved:
            best_schedule = candidate_schedule
            best_evaluation = candidate_evaluation
            no_improvement_cycles = 0

        return GenerationState(
            current_schedule=candidate_schedule,
            best_schedule=best_schedule,
            best_evaluation=best_evaluation,
            cycle_index=state.cycle_index + 1,
            no_improvement_cycles=no_improvement_cycles,
        )

    def _should_continue(self, state: GenerationState) -> bool:
        """Return whether another generation cycle should be executed.

        Args:
            state: Current generator progress snapshot.

        Returns:
            True when the cycle limit and no-improvement limit have not yet been
            reached; otherwise False.
        """
        return (
            state.cycle_index < self.settings.max_cycles
            and state.no_improvement_cycles < self.settings.max_no_improvement_cycles
        )

    def _is_better_candidate(
        self,
        candidate_evaluation: ScheduleEvaluation,
        best_evaluation: ScheduleEvaluation,
    ) -> bool:
        """Compare two evaluations and decide whether the candidate is better.

        Comparison rules:
            1. A valid schedule is always better than an invalid one.
            2. If both have the same validity, the lower total soft score wins.

        Args:
            candidate_evaluation: Evaluation of the new candidate schedule.
            best_evaluation: Evaluation of the best schedule known so far.

        Returns:
            True when the candidate should replace the current best schedule.
        """
        if candidate_evaluation.is_valid != best_evaluation.is_valid:
            return candidate_evaluation.is_valid

        return candidate_evaluation.total_soft_score < best_evaluation.total_soft_score

    def _build_initial_schedule(
        self, workers: list[Worker], start_date: date, end_date: date
    ) -> Schedule:
        """Construct the first schedule used to seed the generation cycle.

        Builds a simple round-robin assignment of workers to shifts across the date range,
        without any regard for constraints. This provides a starting point that is
        guaranteed to be complete, but likely invalid and with a high soft score, which
        the generation cycles can then improve upon.

        Args:
            workers: Workers available for assignment.
            start_date: Inclusive first date of the scheduling window.
            end_date: Inclusive last date of the scheduling window.

        Returns:
            A schedule spanning the requested date range.

        Raises:
            NotImplementedError: The initial construction strategy is not yet
                implemented.
        """
        schedule = Schedule(start_date=start_date, end_date=end_date)
        worker_cycle = cycle(workers)
        current_day = start_date
        while current_day <= end_date:
            for shift_type in ShiftWorkType:
                shift = Shift(
                    shift_type=shift_type, date=current_day, worker=next(worker_cycle)
                )
                schedule.add_shift(shift)
            current_day = next_day(current_day)

        return schedule

    def _build_candidate_schedule(
        self, workers: list[Worker], current_schedule: Schedule
    ) -> Schedule:
        """Create a new candidate schedule from the current schedule.

        Intended future logic:
            Apply one or more generation moves to the current schedule, such as
            swapping assignments, reassigning a day, or rebuilding part of the
            schedule. The goal is to explore a nearby alternative without
            changing the outer generation loop.

        Args:
            workers: Workers available for reassignment.
            current_schedule: Schedule used as the source for the new candidate.

        Returns:
            A new candidate schedule to be repaired, improved, and evaluated.

        Raises:
            NotImplementedError: Candidate generation is not yet implemented.
        """
        raise NotImplementedError("Candidate generation is not implemented yet.")

    def _repair_candidate_schedule(self, schedule: Schedule) -> Schedule:
        """Repair hard-constraint issues in a candidate schedule.

        Intended future logic:
            Inspect the candidate for invalid assignments and apply focused fixes
            that restore feasibility before optimization. This step should prefer
            deterministic repairs that change as little of the schedule as
            possible.

        Args:
            schedule: Candidate schedule that may contain hard-constraint issues.

        Returns:
            A repaired schedule ready for improvement.

        Raises:
            NotImplementedError: Candidate repair is not yet implemented.
        """
        raise NotImplementedError("Candidate repair is not implemented yet.")

    def _improve_candidate_schedule(self, schedule: Schedule) -> Schedule:
        """Improve a repaired schedule without breaking the generation contract.

        Intended future logic:
            Apply local improvements that reduce soft-constraint score while
            preserving or improving validity. Typical strategies include greedy
            local search, small neighborhood moves, or score-driven retries.

        Args:
            schedule: Candidate schedule after the repair phase.

        Returns:
            An improved schedule ready for final evaluation in the current cycle.

        Raises:
            NotImplementedError: Candidate improvement is not yet implemented.
        """
        raise NotImplementedError("Candidate improvement is not implemented yet.")


def generate(workers: list[Worker], start_date: date, end_date: date) -> Schedule:
    """Convenience entry point for schedule generation.

    Args:
        workers: Workers available for assignment.
        start_date: Inclusive first date of the scheduling window.
        end_date: Inclusive last date of the scheduling window.

    Returns:
        The best schedule found by the default ScheduleGenerator instance.
    """
    generator = ScheduleGenerator()
    return generator.generate(workers, start_date, end_date)