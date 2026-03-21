from datetime import date

try:
    from constraints.soft import balanced_schedule
    from model.schedule import Schedule
    from model.shift import Shift
    from model.shift_type import ShiftWorkType
    from model.worker import Worker
except ModuleNotFoundError:
    from src.constraints.soft import balanced_schedule
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
