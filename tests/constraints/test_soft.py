from datetime import date

from src.constraints.soft import balanced_schedule, shift_continuation
from src.model.schedule import Schedule
from src.model.shift import Shift
from src.model.shift_type import ShiftWorkType
from src.model.worker import Worker


def test_balanced_schedule_real_objects():
    Worker.reset_ids()
    w1 = Worker("Alice")
    w2 = Worker("Bob")
    sched = Schedule(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 3),
    )
    # Assign shifts: Alice gets 1 morning, 1 afternoon, 1 night; Bob gets 2 mornings, 1 night
    sched.add_shift(Shift(ShiftWorkType.MORNING, date(2024, 1, 1), w1))
    sched.add_shift(Shift(ShiftWorkType.AFTERNOON, date(2024, 1, 2), w1))
    sched.add_shift(Shift(ShiftWorkType.NIGHT, date(2024, 1, 3), w1))
    sched.add_shift(Shift(ShiftWorkType.MORNING, date(2024, 1, 1), w2))
    sched.add_shift(Shift(ShiftWorkType.MORNING, date(2024, 1, 2), w2))
    sched.add_shift(Shift(ShiftWorkType.NIGHT, date(2024, 1, 3), w2))
    result = balanced_schedule(sched)
    assert isinstance(result, float)
    # Alice: [1,1,1], Bob: [2,0,1] (M,A,N)
    # Averages: M=1.5, A=0.5, N=1.0
    # Alice: |1-1.5|+|1-0.5|+|1-1| = 0.5+0.5+0 = 1.0
    # Bob:   |2-1.5|+|0-0.5|+|1-1| = 0.5+0.5+0 = 1.0
    # Total = 2.0
    assert abs(result - 2.0) < 1e-6

def test_balanced_schedule_perfect_balance():
    Worker.reset_ids()
    w1 = Worker("A")
    w2 = Worker("B")
    sched = Schedule(start_date=date(2024, 1, 1), end_date=date(2024, 1, 3))
    # Both get 1 of each shift type
    for st, d in zip([ShiftWorkType.MORNING, ShiftWorkType.AFTERNOON, ShiftWorkType.NIGHT], [1,2,3]):
        sched.add_shift(Shift(st, date(2024, 1, d), w1))
        sched.add_shift(Shift(st, date(2024, 1, d), w2))
    result = balanced_schedule(sched)
    assert abs(result) < 1e-6

def test_balanced_schedule_single_worker():
    Worker.reset_ids()
    w1 = Worker("Solo")
    sched = Schedule(start_date=date(2024, 1, 1), end_date=date(2024, 1, 3))
    sched.add_shift(Shift(ShiftWorkType.MORNING, date(2024, 1, 1), w1))
    sched.add_shift(Shift(ShiftWorkType.AFTERNOON, date(2024, 1, 2), w1))
    sched.add_shift(Shift(ShiftWorkType.NIGHT, date(2024, 1, 3), w1))
    result = balanced_schedule(sched)
    assert abs(result) < 1e-6

def test_balanced_schedule_no_shifts():
    Worker.reset_ids()
    sched = Schedule(start_date=date(2024, 1, 1), end_date=date(2024, 1, 3))
    # No shifts assigned
    result = balanced_schedule(sched)
    assert abs(result) < 1e-6


# --- shift_continuation tests ---
def test_shift_continuation_no_changes():
    Worker.reset_ids()
    w = Worker("A")
    sched = Schedule(start_date=date(2024, 1, 1), end_date=date(2024, 1, 3))
    # All shifts are the same type, consecutive days
    sched.add_shift(Shift(ShiftWorkType.MORNING, date(2024, 1, 1), w))
    sched.add_shift(Shift(ShiftWorkType.MORNING, date(2024, 1, 2), w))
    sched.add_shift(Shift(ShiftWorkType.MORNING, date(2024, 1, 3), w))
    result = shift_continuation(sched)
    assert abs(result) < 1e-6


def test_shift_continuation_with_changes():
    Worker.reset_ids()
    w = Worker("B")
    sched = Schedule(start_date=date(2024, 1, 1), end_date=date(2024, 1, 4))
    # Morning -> Afternoon -> Night (all changes, last is night)
    sched.add_shift(Shift(ShiftWorkType.MORNING, date(2024, 1, 1), w))
    sched.add_shift(Shift(ShiftWorkType.AFTERNOON, date(2024, 1, 2), w))
    sched.add_shift(Shift(ShiftWorkType.NIGHT, date(2024, 1, 3), w))
    # Penalties: M->A (1.0), A->N (night, 1.0)
    result = shift_continuation(sched)
    assert abs(result - 2.0) < 1e-6


def test_shift_continuation_night_involved():
    Worker.reset_ids()
    w = Worker("C")
    sched = Schedule(start_date=date(2024, 1, 1), end_date=date(2024, 1, 4))
    # Night -> Morning -> Night
    sched.add_shift(Shift(ShiftWorkType.NIGHT, date(2024, 1, 1), w))
    sched.add_shift(Shift(ShiftWorkType.MORNING, date(2024, 1, 2), w))
    sched.add_shift(Shift(ShiftWorkType.NIGHT, date(2024, 1, 3), w))
    # Penalties: N->M (night, 1.0), M->N (night, 1.0)
    result = shift_continuation(sched)
    assert abs(result - 2.0) < 1e-6


def test_shift_continuation_multiple_workers():
    Worker.reset_ids()
    w1 = Worker("A")
    w2 = Worker("B")
    sched = Schedule(start_date=date(2024, 1, 1), end_date=date(2024, 1, 4))
    # w1: M->A->N (2 changes)
    sched.add_shift(Shift(ShiftWorkType.MORNING, date(2024, 1, 1), w1))
    sched.add_shift(Shift(ShiftWorkType.AFTERNOON, date(2024, 1, 2), w1))
    sched.add_shift(Shift(ShiftWorkType.NIGHT, date(2024, 1, 3), w1))
    # w2: N->N->A (1 change, N->A)
    sched.add_shift(Shift(ShiftWorkType.NIGHT, date(2024, 1, 1), w2))
    sched.add_shift(Shift(ShiftWorkType.NIGHT, date(2024, 1, 2), w2))
    sched.add_shift(Shift(ShiftWorkType.AFTERNOON, date(2024, 1, 3), w2))
    result = shift_continuation(sched)
    # w1: M->A (1.0), A->N (night, 1.0) = 2.0; w2: N->N (0), N->A (night, 1.0) = 1.0; total = 3.0
    assert abs(result - 3.0) < 1e-6


def test_shift_continuation_single_worker_no_shifts():
    Worker.reset_ids()
    w = Worker("Solo")
    sched = Schedule(start_date=date(2024, 1, 1), end_date=date(2024, 1, 3))
    # No shifts assigned
    result = shift_continuation(sched)
    assert abs(result) < 1e-6
