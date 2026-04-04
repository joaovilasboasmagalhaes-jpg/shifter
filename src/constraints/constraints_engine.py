from src.constraints.hard import five_consecutive_shifts, rest_gap
from src.constraints.soft import (
    balanced_schedule,
    monthly_weekend,
    preferred_schedule,
    shift_continuation,
)
from src.model.schedule import Schedule


def _run_hard_constraints(schedule: Schedule):

    five_consecutive_shifts(schedule)
    rest_gap(schedule)

def _run_soft_constraints(schedule: Schedule):

    schedule_scores: dict[str, float] = {}
    schedule_scores["balanced_schedule"] = balanced_schedule(schedule)
    schedule_scores["shift_continuation"] = shift_continuation(schedule)
    schedule_scores["preferred_schedule"] = preferred_schedule(schedule, schedule)
    schedule_scores["monthly_weekend"] = monthly_weekend(schedule)

def evaluate(schedule: Schedule):
    _run_hard_constraints(schedule)
    _run_soft_constraints(schedule)
    
    return