from datetime import date, timedelta

import pytest

from src.constraints.hard import five_consecutive_shifts, monthly_weekend, rest_gap
from src.constraints.violation import ConstraintSeverity, collector
from src.model.schedule import Schedule
from src.model.shift import Shift
from src.model.shift_type import ShiftBreakType, ShiftWorkType
from src.model.worker import Worker


@pytest.fixture(autouse=True)
def reset_state():
    Worker.reset_ids()
    collector.clear()
    yield
    Worker.reset_ids()
    collector.clear()


def make_schedule(*dates: date, worker: Worker) -> Schedule:
    start = min(dates)
    end = max(dates)
    sched = Schedule(start_date=start, end_date=end)
    for d in dates:
        sched.add_shift(Shift(shift_type=ShiftWorkType.MORNING, date=d, worker=worker))
    return sched


def consecutive_dates(start: date, count: int) -> list[date]:
    return [start + timedelta(days=i) for i in range(count)]


def test_no_shifts_returns_false():
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    assert five_consecutive_shifts(sched) is False
    assert collector.violations == []


def test_five_consecutive_shifts_allowed():
    worker = Worker(name="Alice")
    dates = consecutive_dates(date(2026, 3, 1), 5)
    sched = make_schedule(*dates, worker=worker)
    assert five_consecutive_shifts(sched) is False
    assert collector.violations == []


def test_six_consecutive_shifts_violation():
    worker = Worker(name="Bob")
    dates = consecutive_dates(date(2026, 3, 1), 6)
    sched = make_schedule(*dates, worker=worker)
    assert five_consecutive_shifts(sched) is True
    assert len(collector.violations) == 1
    v = collector.violations[0]
    assert v.constraint_name == "Five Consecutive Shifts"
    assert v.severity == ConstraintSeverity.ERROR
    assert v.worker_id == worker.id
    assert "consecutive_shifts" in v.details
    assert len(v.details["consecutive_shifts"]) == 6


def test_gap_resets_consecutive_count():
    worker = Worker(name="Carol")
    # 5 consecutive, gap of one day, then 5 more — no violation
    dates = consecutive_dates(date(2026, 3, 1), 5) + consecutive_dates(date(2026, 3, 7), 5)
    sched = make_schedule(*dates, worker=worker)
    assert five_consecutive_shifts(sched) is False


def test_gap_then_six_consecutive_is_violation():
    worker = Worker(name="Diana")
    dates = consecutive_dates(date(2026, 3, 1), 5) + consecutive_dates(date(2026, 3, 7), 6)
    sched = make_schedule(*dates, worker=worker)
    assert five_consecutive_shifts(sched) is True
    assert len(collector.violations) == 1
    assert collector.violations[0].worker_id == worker.id


def test_only_offending_worker_triggers_violation():
    worker_ok = Worker(name="Eve")
    worker_bad = Worker(name="Frank")
    start = date(2026, 3, 1)
    end = date(2026, 3, 31)
    sched = Schedule(start_date=start, end_date=end)
    # worker_ok has exactly 5 consecutive — fine
    for d in consecutive_dates(date(2026, 3, 1), 5):
        sched.add_shift(Shift(shift_type=ShiftWorkType.MORNING, date=d, worker=worker_ok))
    # worker_bad has 6 consecutive — violation
    for d in consecutive_dates(date(2026, 3, 10), 6):
        sched.add_shift(Shift(shift_type=ShiftWorkType.MORNING, date=d, worker=worker_bad))
    assert five_consecutive_shifts(sched) is True
    assert len(collector.violations) == 1
    assert collector.violations[0].worker_id == worker_bad.id


def test_single_shift_no_violation():
    worker = Worker(name="Grace")
    sched = make_schedule(date(2026, 3, 15), worker=worker)
    assert five_consecutive_shifts(sched) is False


def test_monthly_weekend_breaks_when_worker_works_all_weekends_in_month():
    worker = Worker(name="Henry")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    # March 2026 weekends: (7,8), (14,15), (21,22), (28,29)
    worked_days = [date(2026, 3, 7), date(2026, 3, 14), date(2026, 3, 21), date(2026, 3, 28)]
    for d in worked_days:
        sched.add_shift(Shift(shift_type=ShiftWorkType.MORNING, date=d, worker=worker))

    assert monthly_weekend(sched) is True
    assert len(collector.violations) == 1
    violation = collector.violations[0]
    assert violation.constraint_name == "Monthly Weekend Off"
    assert violation.severity == ConstraintSeverity.ERROR
    assert violation.worker_id == worker.id


def test_monthly_weekend_does_not_break_when_worker_has_one_full_weekend_off():
    worker = Worker(name="Iris")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    # Works in 3 weekends only; one weekend has no work shift.
    worked_days = [date(2026, 3, 7), date(2026, 3, 14), date(2026, 3, 21)]
    for d in worked_days:
        sched.add_shift(Shift(shift_type=ShiftWorkType.MORNING, date=d, worker=worker))

    assert monthly_weekend(sched) is False
    warnings = [
        v for v in collector.violations if v.severity == ConstraintSeverity.WARNING
    ]
    assert len(warnings) == 1
    assert warnings[0].worker_id == worker.id


def test_monthly_weekend_does_not_break_for_partial_month_schedule():
    worker = Worker(name="Jo")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 15))
    # Worker covers all weekends that exist in the partial schedule period,
    # but not all weekends in the full month.
    worked_days = [date(2026, 3, 7), date(2026, 3, 14)]
    for d in worked_days:
        sched.add_shift(Shift(shift_type=ShiftWorkType.MORNING, date=d, worker=worker))

    assert monthly_weekend(sched) is False
    warnings = [
        v for v in collector.violations if v.severity == ConstraintSeverity.WARNING
    ]
    assert len(warnings) == 2
    assert all(v.worker_id == worker.id for v in warnings)


def test_monthly_weekend_counts_only_work_shifts_for_weekend_coverage():
    worker = Worker(name="Kai")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    # Day off on the last weekend should not count as working.
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 7), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 14), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 21), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftBreakType.DAY_OFF, date=date(2026, 3, 28), worker=worker)
    )

    assert monthly_weekend(sched) is False
    assert collector.violations == []


def test_monthly_weekend_warns_when_weekend_data_is_missing():
    worker = Worker(name="Lia")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    # Only one weekend has data; remaining weekends should trigger warnings.
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 7), worker=worker)
    )

    assert monthly_weekend(sched) is False

    warnings = [
        v for v in collector.violations if v.severity == ConstraintSeverity.WARNING
    ]
    assert len(warnings) == 3
    assert all(v.worker_id == worker.id for v in warnings)


def test_monthly_weekend_treats_two_break_days_as_full_weekend_off():
    worker = Worker(name="Mona")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    # Works every weekend except the last one, where both weekend days are breaks.
    for d in [date(2026, 3, 7), date(2026, 3, 14), date(2026, 3, 21)]:
        sched.add_shift(Shift(shift_type=ShiftWorkType.MORNING, date=d, worker=worker))
    sched.add_shift(
        Shift(shift_type=ShiftBreakType.DAY_OFF, date=date(2026, 3, 28), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftBreakType.DAY_OFF, date=date(2026, 3, 29), worker=worker)
    )

    assert monthly_weekend(sched) is False
    assert collector.violations == []


def test_monthly_weekend_marks_mixed_work_and_break_weekend_as_working():
    worker = Worker(name="Nora")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    # Each weekend has at least one work shift, even if the other day is a break.
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 7), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftBreakType.DAY_OFF, date=date(2026, 3, 8), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 14), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftBreakType.DAY_OFF, date=date(2026, 3, 15), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 21), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftBreakType.DAY_OFF, date=date(2026, 3, 22), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 28), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftBreakType.DAY_OFF, date=date(2026, 3, 29), worker=worker)
    )

    assert monthly_weekend(sched) is True
    assert len(collector.violations) == 1
    violation = collector.violations[0]
    assert violation.severity == ConstraintSeverity.ERROR
    assert violation.worker_id == worker.id


# Rest Gap Constraint Tests


def test_rest_gap_no_shifts_returns_false():
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    assert rest_gap(sched) is False
    assert collector.violations == []


def test_rest_gap_single_shift_returns_false():
    worker = Worker(name="Alice")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 15), worker=worker)
    )
    assert rest_gap(sched) is False
    assert collector.violations == []


def test_rest_gap_two_shifts_with_24_hours_rest_allowed():
    """A 24-hour gap between work shifts should not raise a violation."""
    worker = Worker(name="Bob")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.NIGHT, date=date(2026, 3, 1), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 2), worker=worker)
    )
    assert rest_gap(sched) is False
    assert collector.violations == []


def test_rest_gap_two_shifts_with_16_hours_rest_allowed():
    """A 16-hour gap between work shifts should not raise a violation."""
    worker = Worker(name="Carol")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.AFTERNOON, date=date(2026, 3, 1), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.AFTERNOON, date=date(2026, 3, 2), worker=worker)
    )
    assert rest_gap(sched) is False
    assert collector.violations == []


def test_rest_gap_violation_insufficient_rest():
    """AFTERNOON (16-24) on day 1, MORNING (8-16) on day 2 = 8 hours rest (VIOLATION)."""
    worker = Worker(name="Diana")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.AFTERNOON, date=date(2026, 3, 1), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 2), worker=worker)
    )
    assert rest_gap(sched) is True
    assert len(collector.violations) == 1
    violation = collector.violations[0]
    assert violation.constraint_name == "Rest Gap"
    assert violation.severity == ConstraintSeverity.ERROR
    assert violation.worker_id == worker.id
    assert violation.details["hours_between"] == 8


def test_rest_gap_break_does_not_trigger_gap_check():
    """Work-to-break and break-to-work should not be checked."""
    worker = Worker(name="Eve")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.AFTERNOON, date=date(2026, 3, 1), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftBreakType.DAY_OFF, date=date(2026, 3, 2), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 3), worker=worker)
    )
    assert rest_gap(sched) is False
    assert collector.violations == []


def test_rest_gap_multiple_violations_same_worker():
    """Same worker with multiple insufficient rest gaps."""
    worker = Worker(name="Frank")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    # Violation 1: AFTERNOON day 1, MORNING day 2 (8 hours)
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.AFTERNOON, date=date(2026, 3, 1), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 2), worker=worker)
    )
    # Violation 2: MORNING day 2, MORNING day 3 (24 hours - OK actually, should be no violation)
    # Let me use MORNING day 2, then NIGHT day 3 for another violation
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.NIGHT, date=date(2026, 3, 3), worker=worker)
    )
    # MORNING (8-16) to NIGHT (0-8) = 1 * 24 + (0 - 16) = 8 hours -- VIOLATION

    assert rest_gap(sched) is True
    assert len(collector.violations) == 2
    assert all(v.worker_id == worker.id for v in collector.violations)
    assert collector.violations[0].details["hours_between"] == 8
    assert collector.violations[1].details["hours_between"] == 8


def test_rest_gap_only_violating_worker_flagged():
    """Multiple workers; only the one with violation is flagged."""
    worker_ok = Worker(name="Grace")
    worker_bad = Worker(name="Henry")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))

    # worker_ok: adequate rest
    sched.add_shift(
        Shift(
            shift_type=ShiftWorkType.AFTERNOON, date=date(2026, 3, 1), worker=worker_ok
        )
    )
    sched.add_shift(
        Shift(
            shift_type=ShiftWorkType.AFTERNOON, date=date(2026, 3, 2), worker=worker_ok
        )
    )

    # worker_bad: insufficient rest
    sched.add_shift(
        Shift(
            shift_type=ShiftWorkType.AFTERNOON,
            date=date(2026, 3, 10),
            worker=worker_bad,
        )
    )
    sched.add_shift(
        Shift(
            shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 11), worker=worker_bad
        )
    )

    assert rest_gap(sched) is True
    assert len(collector.violations) == 1
    assert collector.violations[0].worker_id == worker_bad.id


def test_rest_gap_longer_than_minimum_allowed():
    """A gap comfortably above the minimum should not raise a violation."""
    worker = Worker(name="Iris")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 1), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.AFTERNOON, date=date(2026, 3, 2), worker=worker)
    )
    assert rest_gap(sched) is False
    assert collector.violations == []


def test_rest_gap_preserves_shift_details_in_violations():
    """Violation details include shift information for debugging."""
    worker = Worker(name="Jack")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.AFTERNOON, date=date(2026, 3, 5), worker=worker)
    )
    sched.add_shift(
        Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 6), worker=worker)
    )

    assert rest_gap(sched) is True
    assert len(collector.violations) == 1
    violation = collector.violations[0]
    assert "previous_shift" in violation.details
    assert "current_shift" in violation.details
    assert "hours_between" in violation.details
