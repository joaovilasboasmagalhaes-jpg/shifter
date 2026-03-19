from datetime import date

import pytest

from src.model.schedule import Schedule
from src.model.shift import Shift
from src.model.shift_type import ShiftBreakType, ShiftWorkType
from src.model.worker import Worker


def test_add_shift_within_range():
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    w = Worker(name="Alice")
    s = Shift(shift_type=ShiftWorkType.NIGHT, date=date(2026, 3, 14), worker=w)
    sched.add_shift(s)
    assert len(sched.shifts_by_worker[w.id]) == 1
    assert sched.shifts_on(date(2026, 3, 14)) == [s]


def test_add_shift_out_of_range_raises():
    sched = Schedule(start_date=date(2026, 3, 10), end_date=date(2026, 3, 20))
    w = Worker(name="Bob")
    s = Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 9), worker=w)
    with pytest.raises(ValueError):
        sched.add_shift(s)


def test_schedule_str_and_counts():
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    w = Worker(name="Carol")
    s1 = Shift(shift_type=ShiftWorkType.AFTERNOON, date=date(2026, 3, 5), worker=w)
    s2 = Shift(shift_type=ShiftBreakType.VACATION, date=date(2026, 3, 6), worker=w)
    sched.add_shift(s1)
    sched.add_shift(s2)
    assert "2026-03-01" in str(sched)
    assert "(2 shifts)" in sched.to_string()


def test_shifts_on_out_of_range_raises():
    sched = Schedule(start_date=date(2026, 3, 10), end_date=date(2026, 3, 20))
    # asking for shifts on a date outside the schedule should raise
    with pytest.raises(ValueError):
        sched.shifts_on(date(2026, 3, 9))


def test_shifts_for_worker_returns_only_requested_worker_shifts():
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
    w1 = Worker(name="Diana")
    w2 = Worker(name="Evan")
    s1 = Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 8), worker=w1)
    s2 = Shift(shift_type=ShiftWorkType.NIGHT, date=date(2026, 3, 9), worker=w1)
    s3 = Shift(shift_type=ShiftBreakType.DAY_OFF, date=date(2026, 3, 9), worker=w2)

    sched.add_shift(s1)
    sched.add_shift(s2)
    sched.add_shift(s3)

    assert sched.shifts_for_worker(w1.id) == [s1, s2]
    assert sched.shifts_for_worker(w2.id) == [s3]


def test_shifts_for_worker_returns_empty_list_when_worker_has_no_shifts():
    sched = Schedule(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))

    assert sched.shifts_for_worker(9999) == []
