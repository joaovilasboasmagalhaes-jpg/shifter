from datetime import date, timedelta

import pytest

from src.constraints.hard import five_consecutive_shifts, monthly_weekend
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
    assert collector.violations == []


def test_monthly_weekend_does_not_break_for_partial_month_schedule():
    worker = Worker(name="Jo")
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 15))
    # Worker covers all weekends that exist in the partial schedule period,
    # but not all weekends in the full month.
    worked_days = [date(2026, 3, 7), date(2026, 3, 14)]
    for d in worked_days:
        sched.add_shift(Shift(shift_type=ShiftWorkType.MORNING, date=d, worker=worker))

    assert monthly_weekend(sched) is False
    assert collector.violations == []


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
