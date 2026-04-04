from src.constraints.hard import five_consecutive_shifts, rest_gap
from src.constraints.soft import (
    balanced_schedule,
    monthly_weekend,
    preferred_schedule,
    shift_continuation,
)
from src.constraints.violation import Constraint


# Dummy Schedule for logic tests (replace with real Schedule as needed)
class DummySchedule:
    shifts_by_worker = {}
    def get_worker(self, worker_id):
        return None
    def get_shift(self, worker_id, date):
        return None

def test_hard_constraint_metadata():
    assert isinstance(five_consecutive_shifts, Constraint)
    assert five_consecutive_shifts.title == "Five Consecutive Shifts"
    assert five_consecutive_shifts.is_hard is True
    assert isinstance(rest_gap, Constraint)
    assert rest_gap.title == "Rest Gap"
    assert rest_gap.is_hard is True

def test_soft_constraint_metadata():
    for constraint, title in [
        (balanced_schedule, "Balanced Schedule"),
        (shift_continuation, "Shift Continuation"),
        (preferred_schedule, "Preferred Schedule"),
        (monthly_weekend, "Monthly Weekend"),
    ]:
        assert isinstance(constraint, Constraint)
        assert constraint.title == title
        assert getattr(constraint, 'is_hard', False) is False

def test_constraint_callability():
    # Should be callable and forward to the wrapped function
    schedule = DummySchedule()
    # These should not raise (logic not tested here)
    balanced_schedule(schedule)
    shift_continuation(schedule)
    monthly_weekend(schedule)
    # preferred_schedule needs two schedules
    preferred_schedule(schedule, schedule)
